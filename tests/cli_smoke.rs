// Copyright 2026 Ego Hygiene
// SPDX-License-Identifier: MIT

use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use tempfile::TempDir;

const PROFILES: [&str; 4] = [
    "magazine",
    "nih-nimh-rpg",
    "research-paper",
    "technical-whitepaper",
];

fn beacon_binary() -> PathBuf {
    PathBuf::from(env!("CARGO_BIN_EXE_beacon"))
}

fn templates_directory() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("templates")
}

fn run_beacon(arguments: &[&str]) -> Output {
    Command::new(beacon_binary())
        .arg("--templates-directory")
        .arg(templates_directory())
        .args(arguments)
        .output()
        .expect("failed to execute Beacon CLI")
}

#[test]
fn lists_and_validates_every_active_profile() {
    let list = run_beacon(&["list"]);
    assert!(
        list.status.success(),
        "list failed: {}",
        String::from_utf8_lossy(&list.stderr)
    );
    let stdout = String::from_utf8_lossy(&list.stdout);
    let positions = PROFILES
        .iter()
        .map(|profile| stdout.find(profile).expect("profile missing from list"))
        .collect::<Vec<_>>();
    assert!(positions.windows(2).all(|pair| pair[0] < pair[1]));

    let validate = run_beacon(&["validate"]);
    assert!(
        validate.status.success(),
        "validate failed: {}",
        String::from_utf8_lossy(&validate.stderr)
    );
    let stdout = String::from_utf8_lossy(&validate.stdout);
    for profile in PROFILES {
        assert!(stdout.contains(&format!("valid: {profile}")));
    }
}

#[test]
fn inspects_initializer_and_output_contracts() {
    let output = run_beacon(&["inspect", "magazine"]);
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("id: magazine"));
    assert!(stdout.contains("pdf/digital-review"));
    assert!(stdout.contains("initializer: python3 scripts/bootstrap.py"));
}

#[test]
fn initializes_every_active_profile() {
    let temporary = TempDir::new().expect("failed to create temporary directory");
    for profile in PROFILES {
        let destination = temporary.path().join(profile);
        let destination_text = destination.to_string_lossy().into_owned();
        let output = run_beacon(&[
            "init",
            profile,
            &destination_text,
            "--title",
            "Beacon Initialization Smoke",
            "--author",
            "Beacon Maintainers",
            "--project-id",
            "beacon-init-smoke",
        ]);
        assert!(
            output.status.success(),
            "{profile} init failed: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        let project_manifest = destination.join("beacon-project.toml");
        assert!(project_manifest.is_file(), "{profile} manifest missing");
        let manifest = fs::read_to_string(project_manifest).expect("failed to read manifest");
        assert!(manifest.contains(&format!("profile = \"{profile}\"")));
        assert!(manifest.contains("profile_version = \"0.1.0\""));
    }
}

#[test]
fn refuses_to_overwrite_existing_project_content() {
    let temporary = TempDir::new().expect("failed to create temporary directory");
    let destination = temporary.path().join("existing-project");
    fs::create_dir_all(&destination).expect("failed to create destination");
    fs::write(destination.join("keep.txt"), "preserve me").expect("failed to seed destination");
    let destination_text = destination.to_string_lossy().into_owned();

    let output = run_beacon(&[
        "init",
        "research-paper",
        &destination_text,
        "--title",
        "Should Not Write",
        "--author",
        "Beacon Maintainers",
    ]);

    assert!(!output.status.success());
    assert_eq!(
        fs::read_to_string(destination.join("keep.txt")).expect("seed file disappeared"),
        "preserve me"
    );
    assert!(!destination.join("beacon-project.toml").exists());
}

#[test]
fn preserves_quoted_project_metadata() {
    let temporary = TempDir::new().expect("failed to create temporary directory");
    let destination = temporary.path().join("quoted-project");
    let destination_text = destination.to_string_lossy().into_owned();
    let output = run_beacon(&[
        "init",
        "research-paper",
        &destination_text,
        "--title",
        "A \"Quoted\" Research Paper",
        "--author",
        "Researcher & Collaborator",
    ]);
    assert!(
        output.status.success(),
        "quoted init failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let manifest = fs::read_to_string(destination.join("beacon-project.toml"))
        .expect("missing project manifest");
    let manifest: toml::Value = toml::from_str(&manifest).expect("invalid generated TOML");
    assert_eq!(
        manifest["paper"]["title"].as_str(),
        Some("A \"Quoted\" Research Paper")
    );
    assert_eq!(
        manifest["paper"]["authors"][0]["name"].as_str(),
        Some("Researcher & Collaborator")
    );
}
