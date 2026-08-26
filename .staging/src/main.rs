// Copyright 2026 Ego Hygiene
// SPDX-License-Identifier: MIT

use anyhow::{bail, Context, Result};
use clap::{Parser, Subcommand};
use serde::Deserialize;
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Parser, Debug)]
#[command(name = "beacon", version, about = "Bootstrap reproducible projects from versioned templates")]
struct Cli {
    #[arg(long, default_value = "templates")]
    templates_directory: PathBuf,

    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand, Debug)]
enum Command {
    /// List discovered template packages.
    List,
    /// Inspect one template package.
    Inspect { template_id: String },
    /// Validate one template package or every discovered package.
    Validate { template_id: Option<String> },
    /// Initialize a new project from a template package.
    Init {
        template_id: String,
        destination: PathBuf,
        #[arg(long)]
        title: String,
        #[arg(long)]
        author: String,
    },
}

#[derive(Debug, Deserialize)]
struct TemplateManifest {
    schema_version: u32,
    id: String,
    name: String,
    version: String,
    description: String,
    category: String,
    license: String,
    source: String,
    outputs: Vec<TemplateOutput>,
    metadata: MetadataContract,
    capabilities: BTreeMap<String, bool>,
}

#[derive(Debug, Deserialize)]
struct TemplateOutput {
    format: String,
    renderer: String,
    template: String,
}

#[derive(Debug, Deserialize)]
struct MetadataContract {
    required: Vec<String>,
    optional: Vec<String>,
}

#[derive(Debug)]
struct TemplatePackage {
    directory: PathBuf,
    manifest: TemplateManifest,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let packages = discover_templates(&cli.templates_directory)?;

    match cli.command {
        Command::List => list_templates(&packages),
        Command::Inspect { template_id } => {
            let package = find_template(&packages, &template_id)?;
            inspect_template(package);
            Ok(())
        }
        Command::Validate { template_id } => {
            if let Some(template_id) = template_id {
                validate_package(find_template(&packages, &template_id)?)?;
                println!("valid: {template_id}");
            } else {
                for package in &packages {
                    validate_package(package)?;
                    println!("valid: {}", package.manifest.id);
                }
            }
            Ok(())
        }
        Command::Init {
            template_id,
            destination,
            title,
            author,
        } => initialize_project(
            find_template(&packages, &template_id)?,
            &destination,
            &title,
            &author,
        ),
    }
}

fn discover_templates(root: &Path) -> Result<Vec<TemplatePackage>> {
    if !root.is_dir() {
        bail!("template directory does not exist: {}", root.display());
    }

    let mut packages = Vec::new();
    for entry in fs::read_dir(root).with_context(|| format!("failed to read {}", root.display()))? {
        let entry = entry?;
        let directory = entry.path();
        if !directory.is_dir() {
            continue;
        }

        let manifest_path = directory.join("beacon-template.toml");
        if !manifest_path.is_file() {
            continue;
        }

        packages.push(TemplatePackage {
            manifest: read_manifest(&manifest_path)?,
            directory,
        });
    }

    packages.sort_by(|left, right| left.manifest.id.cmp(&right.manifest.id));
    Ok(packages)
}

fn read_manifest(path: &Path) -> Result<TemplateManifest> {
    let content = fs::read_to_string(path)
        .with_context(|| format!("failed to read template manifest {}", path.display()))?;
    toml::from_str(&content)
        .with_context(|| format!("invalid template manifest {}", path.display()))
}

fn find_template<'a>(packages: &'a [TemplatePackage], template_id: &str) -> Result<&'a TemplatePackage> {
    packages
        .iter()
        .find(|package| package.manifest.id == template_id)
        .with_context(|| format!("unknown template: {template_id}"))
}

fn list_templates(packages: &[TemplatePackage]) -> Result<()> {
    for package in packages {
        println!(
            "{}\t{}\t{}\t{}",
            package.manifest.id,
            package.manifest.version,
            package.manifest.category,
            package.manifest.name
        );
    }
    Ok(())
}

fn inspect_template(package: &TemplatePackage) {
    let manifest = &package.manifest;
    println!("id: {}", manifest.id);
    println!("name: {}", manifest.name);
    println!("version: {}", manifest.version);
    println!("schema-version: {}", manifest.schema_version);
    println!("category: {}", manifest.category);
    println!("description: {}", manifest.description);
    println!("license: {}", manifest.license);
    println!("source: {}", manifest.source);
    println!("required-metadata: {}", manifest.metadata.required.join(", "));
    println!("optional-metadata: {}", manifest.metadata.optional.join(", "));
    println!("outputs:");
    for output in &manifest.outputs {
        println!("  - {} via {} ({})", output.format, output.renderer, output.template);
    }
    println!("capabilities:");
    for (name, enabled) in &manifest.capabilities {
        println!("  - {name}: {enabled}");
    }
}

fn validate_package(package: &TemplatePackage) -> Result<()> {
    let manifest = &package.manifest;
    if manifest.schema_version != 1 {
        bail!(
            "template {} uses unsupported schema version {}",
            manifest.id,
            manifest.schema_version
        );
    }
    if manifest.id.trim().is_empty() || manifest.name.trim().is_empty() || manifest.version.trim().is_empty() {
        bail!("template manifest identity fields must not be empty");
    }
    if manifest.outputs.is_empty() {
        bail!("template {} declares no outputs", manifest.id);
    }

    for output in &manifest.outputs {
        let path = package.directory.join(&output.template);
        if !path.is_file() {
            bail!(
                "template {} references missing output template {}",
                manifest.id,
                path.display()
            );
        }
    }

    for required in ["title", "author"] {
        if !manifest.metadata.required.iter().any(|field| field == required) {
            bail!("template {} must require metadata field {required}", manifest.id);
        }
    }

    let example = package.directory.join("example/paper.md");
    if !example.is_file() {
        bail!("template {} is missing example/paper.md", manifest.id);
    }

    Ok(())
}

fn initialize_project(package: &TemplatePackage, destination: &Path, title: &str, author: &str) -> Result<()> {
    validate_package(package)?;

    if destination.exists() {
        let mut entries = fs::read_dir(destination)
            .with_context(|| format!("failed to inspect {}", destination.display()))?;
        if entries.next().transpose()?.is_some() {
            bail!("destination is not empty: {}", destination.display());
        }
    } else {
        fs::create_dir_all(destination)
            .with_context(|| format!("failed to create {}", destination.display()))?;
    }

    let templates_destination = destination.join("templates");
    fs::create_dir_all(&templates_destination)?;
    for output in &package.manifest.outputs {
        fs::copy(
            package.directory.join(&output.template),
            templates_destination.join(&output.template),
        )?;
    }

    let example = fs::read_to_string(package.directory.join("example/paper.md"))?;
    let manuscript = replace_front_matter_values(&example, title, author);
    fs::write(destination.join("paper.md"), manuscript)?;
    fs::write(destination.join("references.bib"), "")?;
    fs::create_dir_all(destination.join("figures"))?;
    fs::create_dir_all(destination.join("data"))?;
    fs::create_dir_all(destination.join("research/notes"))?;
    fs::create_dir_all(destination.join("research/sources"))?;

    let project_manifest = format!(
        "schema_version = 1\ntemplate = \"{}\"\ntemplate_version = \"{}\"\ntitle = {}\nauthor = {}\n",
        package.manifest.id,
        package.manifest.version,
        toml::Value::String(title.to_owned()),
        toml::Value::String(author.to_owned())
    );
    fs::write(destination.join("beacon-project.toml"), project_manifest)?;

    println!("initialized {} at {}", package.manifest.id, destination.display());
    Ok(())
}

fn replace_front_matter_values(input: &str, title: &str, author: &str) -> String {
    input
        .lines()
        .map(|line| {
            if line.starts_with("title:") {
                format!("title: \"{}\"", escape_yaml(title))
            } else if line.starts_with("author:") {
                format!("author: \"{}\"", escape_yaml(author))
            } else {
                line.to_owned()
            }
        })
        .collect::<Vec<_>>()
        .join("\n")
        + "\n"
}

fn escape_yaml(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    fn fixture(root: &Path) -> PathBuf {
        let directory = root.join("research-paper");
        fs::create_dir_all(directory.join("example")).unwrap();
        fs::write(directory.join("template.tex"), "template").unwrap();
        fs::write(directory.join("example/paper.md"), "---\ntitle: \"Old\"\nauthor: \"Old\"\n---\n").unwrap();
        fs::write(
            directory.join("beacon-template.toml"),
            r#"schema_version = 1
id = "research-paper"
name = "Research Paper"
version = "0.1.0"
description = "test"
category = "research"
license = "MIT"
source = "fixture"
[[outputs]]
format = "pdf"
renderer = "pandoc"
template = "template.tex"
[metadata]
required = ["title", "author"]
optional = []
[capabilities]
pdf = true
"#,
        )
        .unwrap();
        directory
    }

    #[test]
    fn discovers_and_validates_template() {
        let root = TempDir::new().unwrap();
        fixture(root.path());
        let packages = discover_templates(root.path()).unwrap();
        assert_eq!(packages.len(), 1);
        validate_package(&packages[0]).unwrap();
    }

    #[test]
    fn initializes_project_with_metadata() {
        let root = TempDir::new().unwrap();
        fixture(root.path());
        let packages = discover_templates(root.path()).unwrap();
        let destination = root.path().join("output");
        initialize_project(&packages[0], &destination, "New Title", "New Author").unwrap();
        let manuscript = fs::read_to_string(destination.join("paper.md")).unwrap();
        assert!(manuscript.contains("title: \"New Title\""));
        assert!(manuscript.contains("author: \"New Author\""));
        assert!(destination.join("templates/template.tex").is_file());
        assert!(destination.join("beacon-project.toml").is_file());
    }

    #[test]
    fn refuses_nonempty_destination() {
        let root = TempDir::new().unwrap();
        fixture(root.path());
        let packages = discover_templates(root.path()).unwrap();
        let destination = root.path().join("output");
        fs::create_dir_all(&destination).unwrap();
        fs::write(destination.join("existing.txt"), "keep").unwrap();
        assert!(initialize_project(&packages[0], &destination, "Title", "Author").is_err());
    }
}
