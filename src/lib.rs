// Copyright 2026 Ego Hygiene
// SPDX-License-Identifier: MIT

//! Beacon's profile registry, manifest validation, and safe initialization core.

use anyhow::{Context, Result, bail};
use serde::Deserialize;
use std::collections::{BTreeMap, BTreeSet};
use std::ffi::OsStr;
use std::fs;
use std::path::{Component, Path, PathBuf};
use std::process::Command;

pub const TEMPLATE_SCHEMA_VERSION: u32 = 1;

const INITIALIZER_PARAMETERS: [&str; 7] = [
    "author",
    "destination",
    "edition",
    "project-id",
    "publisher",
    "theme",
    "title",
];

#[derive(Debug, Deserialize)]
pub struct TemplateManifest {
    pub schema_version: u32,
    pub id: String,
    pub name: String,
    pub version: String,
    pub description: String,
    pub category: String,
    pub license: String,
    pub source: String,
    pub outputs: Vec<TemplateOutput>,
    pub metadata: MetadataContract,
    pub capabilities: BTreeMap<String, bool>,
    pub initializer: Option<InitializerContract>,
}

#[derive(Debug, Deserialize)]
pub struct TemplateOutput {
    pub format: String,
    pub renderer: String,
    pub variant: Option<String>,
    pub template: Option<PathBuf>,
    pub entrypoint: Option<PathBuf>,
    pub artifact: Option<PathBuf>,
}

#[derive(Debug, Deserialize)]
pub struct MetadataContract {
    pub required: Vec<String>,
    pub optional: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct InitializerContract {
    pub runtime: String,
    pub script: PathBuf,
    pub required: Vec<String>,
    #[serde(default)]
    pub optional: Vec<String>,
}

#[derive(Debug)]
pub struct TemplatePackage {
    directory: PathBuf,
    manifest: TemplateManifest,
}

impl TemplatePackage {
    #[must_use]
    pub fn directory(&self) -> &Path {
        &self.directory
    }

    #[must_use]
    pub const fn manifest(&self) -> &TemplateManifest {
        &self.manifest
    }
}

#[derive(Debug)]
pub struct Registry {
    root: PathBuf,
    packages: Vec<TemplatePackage>,
}

impl Registry {
    pub fn discover(root: impl AsRef<Path>) -> Result<Self> {
        let root = root.as_ref();
        if !root.is_dir() {
            bail!("template directory does not exist: {}", root.display());
        }

        let mut packages = Vec::new();
        for entry in fs::read_dir(root)
            .with_context(|| format!("failed to read template registry {}", root.display()))?
        {
            let entry = entry?;
            let directory = entry.path();
            if !directory.is_dir() {
                continue;
            }

            let manifest_path = directory.join("beacon-template.toml");
            if !manifest_path.is_file() {
                continue;
            }

            let content = fs::read_to_string(&manifest_path).with_context(|| {
                format!(
                    "failed to read template manifest {}",
                    manifest_path.display()
                )
            })?;
            let manifest = toml::from_str(&content).with_context(|| {
                format!("invalid template manifest {}", manifest_path.display())
            })?;
            packages.push(TemplatePackage {
                directory,
                manifest,
            });
        }

        packages.sort_by(|left, right| left.manifest.id.cmp(&right.manifest.id));
        if packages.is_empty() {
            bail!("no template packages found in {}", root.display());
        }

        let mut identifiers = BTreeSet::new();
        for package in &packages {
            if !identifiers.insert(package.manifest.id.as_str()) {
                bail!("duplicate template id: {}", package.manifest.id);
            }
        }

        Ok(Self {
            root: root.to_path_buf(),
            packages,
        })
    }

    #[must_use]
    pub fn packages(&self) -> &[TemplatePackage] {
        &self.packages
    }

    pub fn find(&self, template_id: &str) -> Result<&TemplatePackage> {
        self.packages
            .iter()
            .find(|package| package.manifest.id == template_id)
            .with_context(|| format!("unknown template: {template_id}"))
    }

    pub fn validate_all(&self) -> Result<()> {
        for package in &self.packages {
            validate_package(package)?;
        }
        Ok(())
    }

    #[must_use]
    pub fn is_builtin(&self) -> bool {
        paths_refer_to_same_location(&self.root, &builtin_templates_directory())
    }

    pub fn initialize(
        &self,
        template_id: &str,
        destination: &Path,
        options: &InitializationOptions,
        allow_executable_initializer: bool,
    ) -> Result<()> {
        let package = self.find(template_id)?;
        validate_package(package)?;

        if !self.is_builtin() && !allow_executable_initializer {
            bail!(
                "refusing to execute an initializer from an external registry; inspect it first and pass --allow-executable-initializer"
            );
        }

        initialize_package(package, destination, options)
    }
}

#[derive(Debug)]
pub struct InitializationOptions {
    pub title: String,
    pub author: String,
    pub publisher: Option<String>,
    pub edition: String,
    pub project_id: Option<String>,
    pub theme: Option<String>,
    pub python: PathBuf,
}

#[must_use]
pub fn builtin_templates_directory() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("templates")
}

pub fn validate_package(package: &TemplatePackage) -> Result<()> {
    validate_identity(package)?;
    validate_outputs(package)?;
    validate_metadata(package)?;
    validate_initializer(package)
}

fn validate_identity(package: &TemplatePackage) -> Result<()> {
    let manifest = &package.manifest;
    if manifest.schema_version != TEMPLATE_SCHEMA_VERSION {
        bail!(
            "template {} uses unsupported schema version {}",
            manifest.id,
            manifest.schema_version
        );
    }
    if !is_kebab_case_identifier(&manifest.id) {
        bail!("template id must be lowercase kebab-case: {}", manifest.id);
    }
    if package.directory.file_name() != Some(OsStr::new(&manifest.id)) {
        bail!(
            "template id '{}' must match directory '{}'",
            manifest.id,
            package.directory.display()
        );
    }
    for (field, value) in [
        ("name", manifest.name.as_str()),
        ("description", manifest.description.as_str()),
        ("category", manifest.category.as_str()),
        ("license", manifest.license.as_str()),
        ("source", manifest.source.as_str()),
    ] {
        if value.trim().is_empty() {
            bail!("template {} has an empty {field}", manifest.id);
        }
    }
    if !is_three_part_version(&manifest.version) {
        bail!(
            "template {} version must use x.y.z semantic versioning",
            manifest.id
        );
    }
    Ok(())
}

fn validate_outputs(package: &TemplatePackage) -> Result<()> {
    let manifest = &package.manifest;
    if manifest.outputs.is_empty() {
        bail!("template {} declares no outputs", manifest.id);
    }

    for (index, output) in manifest.outputs.iter().enumerate() {
        if output.format.trim().is_empty() || output.renderer.trim().is_empty() {
            bail!(
                "template {} output {index} requires format and renderer",
                manifest.id
            );
        }
        if output.template.is_none() && output.entrypoint.is_none() && output.artifact.is_none() {
            bail!(
                "template {} output {index} must declare template, entrypoint, or artifact",
                manifest.id
            );
        }
        if let Some(variant) = &output.variant
            && variant.trim().is_empty()
        {
            bail!(
                "template {} output {index} has an empty variant",
                manifest.id
            );
        }
        for path in [&output.template, &output.entrypoint, &output.artifact]
            .into_iter()
            .flatten()
        {
            validate_relative_path(path, "output path", &manifest.id)?;
        }
        if let Some(template) = &output.template {
            let template_path = package.directory.join(template);
            if !template_path.is_file() {
                bail!(
                    "template {} references missing renderer template {}",
                    manifest.id,
                    template_path.display()
                );
            }
        }
    }
    Ok(())
}

fn validate_metadata(package: &TemplatePackage) -> Result<()> {
    let manifest = &package.manifest;
    validate_string_sets(
        &manifest.metadata.required,
        &manifest.metadata.optional,
        "metadata",
        &manifest.id,
    )?;
    if manifest.metadata.required.is_empty() {
        bail!("template {} declares no required metadata", manifest.id);
    }
    if manifest.capabilities.is_empty() {
        bail!("template {} declares no capabilities", manifest.id);
    }
    Ok(())
}

fn validate_initializer(package: &TemplatePackage) -> Result<()> {
    let manifest = &package.manifest;
    let initializer = manifest
        .initializer
        .as_ref()
        .with_context(|| format!("template {} declares no initializer", manifest.id))?;
    if initializer.runtime != "python3" {
        bail!(
            "template {} uses unsupported initializer runtime {}",
            manifest.id,
            initializer.runtime
        );
    }
    validate_relative_path(&initializer.script, "initializer script", &manifest.id)?;
    let initializer_path = package.directory.join(&initializer.script);
    if !initializer_path.is_file() {
        bail!(
            "template {} references missing initializer {}",
            manifest.id,
            initializer_path.display()
        );
    }
    validate_string_sets(
        &initializer.required,
        &initializer.optional,
        "initializer parameters",
        &manifest.id,
    )?;
    for parameter in initializer.required.iter().chain(&initializer.optional) {
        if !INITIALIZER_PARAMETERS.contains(&parameter.as_str()) {
            bail!(
                "template {} declares unsupported initializer parameter {parameter}",
                manifest.id
            );
        }
    }
    for required in ["destination", "title"] {
        if !initializer.required.iter().any(|field| field == required) {
            bail!(
                "template {} initializer must require {required}",
                manifest.id
            );
        }
    }
    if !initializer
        .required
        .iter()
        .any(|field| field == "author" || field == "publisher")
    {
        bail!(
            "template {} initializer must require author or publisher",
            manifest.id
        );
    }

    Ok(())
}

fn initialize_package(
    package: &TemplatePackage,
    destination: &Path,
    options: &InitializationOptions,
) -> Result<()> {
    let destination = absolute_destination(destination)?;
    ensure_safe_destination(&destination, package)?;

    let parent = destination.parent().with_context(|| {
        format!(
            "destination must have a writable parent: {}",
            destination.display()
        )
    })?;
    fs::create_dir_all(parent)
        .with_context(|| format!("failed to create destination parent {}", parent.display()))?;

    let temporary = tempfile::Builder::new()
        .prefix(".beacon-init-")
        .tempdir_in(parent)
        .with_context(|| {
            format!(
                "failed to create temporary workspace in {}",
                parent.display()
            )
        })?;
    let workspace = temporary.path().join("project");
    let initializer = package
        .manifest
        .initializer
        .as_ref()
        .context("validated initializer disappeared")?;
    let script = package.directory.join(&initializer.script);

    let mut command = Command::new(&options.python);
    command.arg(&script).current_dir(&package.directory);
    for parameter in initializer.required.iter().chain(&initializer.optional) {
        if let Some(value) = initializer_value(parameter, &workspace, options) {
            command.arg(format!("--{parameter}")).arg(value);
        } else if initializer.required.contains(parameter) {
            bail!(
                "template {} requires initializer value {parameter}",
                package.manifest.id
            );
        }
    }

    let output = command.output().with_context(|| {
        format!(
            "failed to run {} initializer with {}",
            package.manifest.id,
            options.python.display()
        )
    })?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        bail!(
            "{} initializer failed: {}",
            package.manifest.id,
            stderr.trim()
        );
    }
    if !workspace.is_dir() {
        bail!(
            "{} initializer did not create a project directory",
            package.manifest.id
        );
    }
    if !workspace.join("beacon-project.toml").is_file() {
        bail!(
            "{} initializer did not create beacon-project.toml",
            package.manifest.id
        );
    }

    if destination.exists() {
        fs::remove_dir(&destination).with_context(|| {
            format!(
                "failed to replace empty destination {}",
                destination.display()
            )
        })?;
    }
    fs::rename(&workspace, &destination).with_context(|| {
        format!(
            "failed to finalize initialized project at {}",
            destination.display()
        )
    })?;
    Ok(())
}

fn initializer_value(
    parameter: &str,
    workspace: &Path,
    options: &InitializationOptions,
) -> Option<String> {
    match parameter {
        "destination" => Some(workspace.display().to_string()),
        "title" => Some(options.title.clone()),
        "author" => Some(options.author.clone()),
        "publisher" => Some(
            options
                .publisher
                .clone()
                .unwrap_or_else(|| options.author.clone()),
        ),
        "edition" => Some(options.edition.clone()),
        "project-id" => options.project_id.clone(),
        "theme" => options.theme.clone(),
        _ => None,
    }
}

fn absolute_destination(destination: &Path) -> Result<PathBuf> {
    if destination.as_os_str().is_empty() {
        bail!("destination must not be empty");
    }
    if destination.is_absolute() {
        Ok(destination.to_path_buf())
    } else {
        Ok(std::env::current_dir()
            .context("failed to resolve current directory")?
            .join(destination))
    }
}

fn ensure_safe_destination(destination: &Path, package: &TemplatePackage) -> Result<()> {
    if destination.parent().is_none() || destination == Path::new("/") {
        bail!("refusing unsafe destination: {}", destination.display());
    }

    if destination.exists() {
        let metadata = fs::symlink_metadata(destination)
            .with_context(|| format!("failed to inspect destination {}", destination.display()))?;
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            bail!(
                "destination must be a directory and not a symbolic link: {}",
                destination.display()
            );
        }
        if fs::read_dir(destination)
            .with_context(|| format!("failed to inspect {}", destination.display()))?
            .next()
            .transpose()?
            .is_some()
        {
            bail!("destination is not empty: {}", destination.display());
        }
    }

    for protected in [
        Path::new(env!("CARGO_MANIFEST_DIR")),
        package.directory.as_path(),
    ] {
        if paths_refer_to_same_location(destination, protected) {
            bail!("refusing protected destination: {}", destination.display());
        }
    }
    Ok(())
}

fn paths_refer_to_same_location(left: &Path, right: &Path) -> bool {
    let left = left.canonicalize().unwrap_or_else(|_| left.to_path_buf());
    let right = right.canonicalize().unwrap_or_else(|_| right.to_path_buf());
    left == right
}

fn validate_relative_path(path: &Path, label: &str, template_id: &str) -> Result<()> {
    if path.as_os_str().is_empty()
        || path.is_absolute()
        || path.components().any(|component| {
            matches!(
                component,
                Component::ParentDir | Component::RootDir | Component::Prefix(_)
            )
        })
    {
        bail!(
            "template {template_id} has unsafe {label}: {}",
            path.display()
        );
    }
    Ok(())
}

fn validate_string_sets(
    required: &[String],
    optional: &[String],
    label: &str,
    template_id: &str,
) -> Result<()> {
    let mut values = BTreeSet::new();
    for value in required.iter().chain(optional) {
        if value.trim().is_empty() {
            bail!("template {template_id} has an empty {label} value");
        }
        if !values.insert(value) {
            bail!("template {template_id} repeats {label} value {value}");
        }
    }
    Ok(())
}

fn is_kebab_case_identifier(value: &str) -> bool {
    !value.is_empty()
        && value.split('-').all(|part| {
            !part.is_empty()
                && part
                    .chars()
                    .all(|character| character.is_ascii_lowercase() || character.is_ascii_digit())
        })
}

fn is_three_part_version(value: &str) -> bool {
    let parts = value.split('.').collect::<Vec<_>>();
    parts.len() == 3
        && parts.iter().all(|part| {
            !part.is_empty() && part.chars().all(|character| character.is_ascii_digit())
        })
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    fn write_fixture(root: &Path, identifier: &str) {
        let directory = root.join(identifier);
        fs::create_dir_all(directory.join("scripts")).unwrap();
        fs::write(directory.join("template.tex"), "template").unwrap();
        fs::write(
            directory.join("scripts/bootstrap.py"),
            r#"import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--destination", required=True)
parser.add_argument("--title", required=True)
parser.add_argument("--author", required=True)
args = parser.parse_args()
destination = Path(args.destination)
destination.mkdir(parents=True)
(destination / "beacon-project.toml").write_text(
    f'[beacon]\nschema_version = 1\nprofile = "fixture"\nprofile_version = "0.1.0"\n\n[project]\ntitle = "{args.title}"\nauthor = "{args.author}"\n',
    encoding="utf-8",
)
"#,
        )
        .unwrap();
        fs::write(
            directory.join("beacon-template.toml"),
            format!(
                r#"schema_version = 1
id = "{identifier}"
name = "Fixture"
version = "0.1.0"
description = "Fixture package"
category = "test"
license = "MIT"
source = "test"

[[outputs]]
format = "pdf"
renderer = "latexmk"
template = "template.tex"

[metadata]
required = ["title", "author"]
optional = []

[capabilities]
pdf = true

[initializer]
runtime = "python3"
script = "scripts/bootstrap.py"
required = ["destination", "title", "author"]
optional = []
"#
            ),
        )
        .unwrap();
    }

    #[test]
    fn discovers_in_stable_order_and_validates_packages() {
        let root = TempDir::new().unwrap();
        write_fixture(root.path(), "zeta-paper");
        write_fixture(root.path(), "alpha-paper");
        let registry = Registry::discover(root.path()).unwrap();
        registry.validate_all().unwrap();
        let identifiers = registry
            .packages()
            .iter()
            .map(|package| package.manifest().id.as_str())
            .collect::<Vec<_>>();
        assert_eq!(identifiers, ["alpha-paper", "zeta-paper"]);
    }

    #[test]
    fn refuses_external_initializer_without_explicit_trust() {
        let root = TempDir::new().unwrap();
        write_fixture(root.path(), "fixture");
        let registry = Registry::discover(root.path()).unwrap();
        let destination = root.path().join("output");
        let options = InitializationOptions {
            title: "Title".into(),
            author: "Author".into(),
            publisher: None,
            edition: "1".into(),
            project_id: None,
            theme: None,
            python: PathBuf::from("python3"),
        };
        let error = registry
            .initialize("fixture", &destination, &options, false)
            .unwrap_err();
        assert!(error.to_string().contains("external registry"));
        assert!(!destination.exists());
    }

    #[test]
    fn initializes_external_package_after_explicit_trust() {
        let root = TempDir::new().unwrap();
        write_fixture(root.path(), "fixture");
        let registry = Registry::discover(root.path()).unwrap();
        let destination = root.path().join("output");
        let options = InitializationOptions {
            title: "New Title".into(),
            author: "New Author".into(),
            publisher: None,
            edition: "1".into(),
            project_id: None,
            theme: None,
            python: PathBuf::from("python3"),
        };
        registry
            .initialize("fixture", &destination, &options, true)
            .unwrap();
        let manifest = fs::read_to_string(destination.join("beacon-project.toml")).unwrap();
        assert!(manifest.contains("New Title"));
        assert!(manifest.contains("New Author"));
    }
}
