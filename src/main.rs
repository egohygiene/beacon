// Copyright 2026 Ego Hygiene
// SPDX-License-Identifier: MIT

use anyhow::Result;
use beacon::{InitializationOptions, Registry, builtin_templates_directory, validate_package};
use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(
    name = "beacon",
    version,
    about = "Discover, validate, and initialize reproducible publication projects"
)]
struct Cli {
    /// Template registry directory. Defaults to Beacon's built-in registry.
    #[arg(long, global = true)]
    templates_directory: Option<PathBuf>,

    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand, Debug)]
enum Command {
    /// List discovered publication profiles.
    List,
    /// Inspect one publication profile.
    Inspect { profile: String },
    /// Validate one profile or every discovered profile.
    Validate { profile: Option<String> },
    /// Initialize a new project through a profile-owned initializer.
    Init {
        profile: String,
        destination: PathBuf,
        #[arg(long)]
        title: String,
        #[arg(long)]
        author: String,
        #[arg(long)]
        publisher: Option<String>,
        #[arg(long, default_value = "1")]
        edition: String,
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        theme: Option<String>,
        #[arg(long, env = "BEACON_PYTHON", default_value = "python3")]
        python: PathBuf,
        /// Permit executable initializers from a non-built-in registry.
        #[arg(long)]
        allow_executable_initializer: bool,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let templates_directory = cli
        .templates_directory
        .unwrap_or_else(builtin_templates_directory);
    let registry = Registry::discover(templates_directory)?;

    match cli.command {
        Command::List => {
            list_profiles(&registry);
            Ok(())
        }
        Command::Inspect { profile } => {
            inspect_profile(registry.find(&profile)?);
            Ok(())
        }
        Command::Validate { profile } => {
            if let Some(profile) = profile {
                validate_package(registry.find(&profile)?)?;
                println!("valid: {profile}");
            } else {
                for package in registry.packages() {
                    validate_package(package)?;
                    println!("valid: {}", package.manifest().id);
                }
            }
            Ok(())
        }
        Command::Init {
            profile,
            destination,
            title,
            author,
            publisher,
            edition,
            project_id,
            theme,
            python,
            allow_executable_initializer,
        } => {
            let options = InitializationOptions {
                title,
                author,
                publisher,
                edition,
                project_id,
                theme,
                python,
            };
            registry.initialize(
                &profile,
                &destination,
                &options,
                allow_executable_initializer,
            )?;
            println!("initialized {profile} at {}", destination.display());
            Ok(())
        }
    }
}

fn list_profiles(registry: &Registry) {
    for package in registry.packages() {
        let manifest = package.manifest();
        println!(
            "{}\t{}\t{}\t{}\tinitializer",
            manifest.id, manifest.version, manifest.category, manifest.name
        );
    }
}

fn inspect_profile(package: &beacon::TemplatePackage) {
    let manifest = package.manifest();
    println!("id: {}", manifest.id);
    println!("name: {}", manifest.name);
    println!("version: {}", manifest.version);
    println!("schema-version: {}", manifest.schema_version);
    println!("category: {}", manifest.category);
    println!("description: {}", manifest.description);
    println!("license: {}", manifest.license);
    println!("source: {}", manifest.source);
    println!(
        "required-metadata: {}",
        manifest.metadata.required.join(", ")
    );
    println!(
        "optional-metadata: {}",
        manifest.metadata.optional.join(", ")
    );
    println!("outputs:");
    for output in &manifest.outputs {
        let variant = output
            .variant
            .as_ref()
            .map_or_else(String::new, |variant| format!("/{variant}"));
        let path = output
            .template
            .as_ref()
            .or(output.entrypoint.as_ref())
            .or(output.artifact.as_ref())
            .map_or_else(
                || "unspecified".to_owned(),
                |path| path.display().to_string(),
            );
        println!(
            "  - {}{} via {} ({path})",
            output.format, variant, output.renderer
        );
    }
    println!("capabilities:");
    for (name, enabled) in &manifest.capabilities {
        println!("  - {name}: {enabled}");
    }
    if let Some(initializer) = &manifest.initializer {
        println!(
            "initializer: {} {}",
            initializer.runtime,
            initializer.script.display()
        );
        println!("initializer-required: {}", initializer.required.join(", "));
        println!("initializer-optional: {}", initializer.optional.join(", "));
    }
}
