// Copyright 2026 Ego Hygiene
// SPDX-License-Identifier: MIT

use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use tempfile::TempDir;

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
fn lists_and_validates_builtin_research_template() {
    let list = run_beacon(&["list"]);
    assert!(list.status.success());
    let stdout = String::from_utf8_lossy(&list.stdout);
    assert!(stdout.contains("research-paper"));

    let validate = run_beacon(&["validate", "research-paper"]);
    assert!(validate.status.success());
    let stdout = String::from_utf8_lossy(&validate.stdout);
    assert!(stdout.contains("valid: research-paper"));
}

#[test]
fn initializes_complete_research_workspace() {
    let temporary = TempDir::new().expect("failed to create temporary directory");
    let destination = temporary.path().join("adaptive-audio-paper");
    let destination_text = destination.to_string_lossy().into_owned();

    let output = run_beacon(&[
        "init",
        "research-paper",
        &destination_text,
        "--title",
        "Adaptive Generative Audio",
        "--author",
        "Researcher",
    ]);

    assert!(
        output.status.success(),
        "Beacon init failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    for required_file in [
        "beacon-project.toml",
        "paper.md",
        "references.bib",
        "templates/template.tex",
        "templates/template.html",
    ] {
        assert!(
            destination.join(required_file).is_file(),
            "missing generated file: {required_file}"
        );
    }

    for required_directory in [
        "figures",
        "data",
        "research/notes",
        "research/sources",
    ] {
        assert!(
            destination.join(required_directory).is_dir(),
            "missing generated directory: {required_directory}"
        );
    }

    let project_manifest =
        fs::read_to_string(destination.join("beacon-project.toml")).expect("missing project manifest");
    assert!(project_manifest.contains("template = \"research-paper\""));
    assert!(project_manifest.contains("template_version = \"0.1.0\""));
    assert!(project_manifest.contains("title = \"Adaptive Generative Audio\""));
    assert!(project_manifest.contains("author = \"Researcher\""));

    let manuscript = fs::read_to_string(destination.join("paper.md")).expect("missing manuscript");
    assert!(manuscript.contains("title: \"Adaptive Generative Audio\""));
    assert!(manuscript.contains("author: \"Researcher\""));
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
        "Researcher",
    ]);

    assert!(!output.status.success());
    assert_eq!(
        fs::read_to_string(destination.join("keep.txt")).expect("seed file disappeared"),
        "preserve me"
    );
    assert!(!destination.join("beacon-project.toml").exists());
}
