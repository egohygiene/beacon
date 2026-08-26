// Copyright 2026 Ego Hygiene
// SPDX-License-Identifier: MIT

use anyhow::Result;
use beacon::{
    BuildOptions, BuildPlan, InitializationOptions, Registry, builtin_templates_directory,
    validate_package,
};
use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(
    name = "beacon",
    version,
    about = "Initialize, diagnose, build, and package reproducible publication projects"
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
    /// Check the host tools required by one profile or the full registry.
    Doctor {
        profile: Option<String>,
        /// Permit tool checks declared by a non-built-in registry.
        #[arg(long)]
        allow_executable_adapter: bool,
    },
    /// Resolve and print a project's publication build plan without executing it.
    Plan {
        project: PathBuf,
        #[arg(long)]
        output_directory: Option<PathBuf>,
        #[arg(long)]
        theme: Option<String>,
    },
    /// Build and validate a project through its pinned profile adapter.
    Build {
        project: PathBuf,
        #[arg(long)]
        output_directory: Option<PathBuf>,
        #[arg(long)]
        theme: Option<String>,
        /// Permit executable adapters from a non-built-in registry.
        #[arg(long)]
        allow_executable_adapter: bool,
    },
    /// Build a project and stage its verified publication artifacts.
    Package {
        project: PathBuf,
        #[arg(long)]
        output_directory: Option<PathBuf>,
        #[arg(long)]
        package_directory: Option<PathBuf>,
        #[arg(long)]
        theme: Option<String>,
        /// Permit executable adapters from a non-built-in registry.
        #[arg(long)]
        allow_executable_adapter: bool,
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
        Command::Validate { profile } => validate_profiles(&registry, profile.as_deref()),
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
        } => initialize_project(
            &registry,
            &profile,
            &destination,
            &InitializationOptions {
                title,
                author,
                publisher,
                edition,
                project_id,
                theme,
                python,
            },
            allow_executable_initializer,
        ),
        Command::Doctor {
            profile,
            allow_executable_adapter,
        } => run_doctor(&registry, profile.as_deref(), allow_executable_adapter),
        Command::Plan {
            project,
            output_directory,
            theme,
        } => {
            let plan = create_plan(&registry, &project, output_directory, theme)?;
            print_plan(&plan);
            Ok(())
        }
        Command::Build {
            project,
            output_directory,
            theme,
            allow_executable_adapter,
        } => build_project(
            &registry,
            &project,
            output_directory,
            theme,
            allow_executable_adapter,
        ),
        Command::Package {
            project,
            output_directory,
            package_directory,
            theme,
            allow_executable_adapter,
        } => package_project(
            &registry,
            &project,
            output_directory,
            package_directory.as_deref(),
            theme,
            allow_executable_adapter,
        ),
    }
}

fn validate_profiles(registry: &Registry, profile: Option<&str>) -> Result<()> {
    if let Some(profile) = profile {
        validate_package(registry.find(profile)?)?;
        println!("valid: {profile}");
    } else {
        for package in registry.packages() {
            validate_package(package)?;
            println!("valid: {}", package.manifest().id);
        }
    }
    Ok(())
}

fn initialize_project(
    registry: &Registry,
    profile: &str,
    destination: &std::path::Path,
    options: &InitializationOptions,
    allow_executable_initializer: bool,
) -> Result<()> {
    registry.initialize(profile, destination, options, allow_executable_initializer)?;
    println!("initialized {profile} at {}", destination.display());
    Ok(())
}

fn run_doctor(
    registry: &Registry,
    profile: Option<&str>,
    allow_executable_adapter: bool,
) -> Result<()> {
    let checks = registry.doctor(profile, allow_executable_adapter)?;
    let mut missing = 0;
    for check in checks {
        let status = if check.available { "OK" } else { "MISSING" };
        println!(
            "{status}\t{}\t{}\t{}",
            check.profile, check.command, check.detail
        );
        missing += usize::from(!check.available);
    }
    if missing > 0 {
        anyhow::bail!("doctor found {missing} missing required tool(s)");
    }
    Ok(())
}

fn create_plan(
    registry: &Registry,
    project: &std::path::Path,
    output_directory: Option<PathBuf>,
    theme: Option<String>,
) -> Result<BuildPlan> {
    registry.plan(
        project,
        &BuildOptions {
            output_directory,
            theme,
        },
    )
}

fn build_project(
    registry: &Registry,
    project: &std::path::Path,
    output_directory: Option<PathBuf>,
    theme: Option<String>,
    allow_executable_adapter: bool,
) -> Result<()> {
    let plan = create_plan(registry, project, output_directory, theme)?;
    print_plan(&plan);
    registry.build(&plan, allow_executable_adapter)?;
    println!("built {}", plan.output_directory.display());
    Ok(())
}

fn package_project(
    registry: &Registry,
    project: &std::path::Path,
    output_directory: Option<PathBuf>,
    package_directory: Option<&std::path::Path>,
    theme: Option<String>,
    allow_executable_adapter: bool,
) -> Result<()> {
    let plan = create_plan(registry, project, output_directory, theme)?;
    print_plan(&plan);
    let package = registry.package(&plan, package_directory, allow_executable_adapter)?;
    println!(
        "packaged {} artifact(s) at {}",
        package.artifact_count,
        package.directory.display()
    );
    println!("manifest: {}", package.manifest.display());
    println!("checksums: {}", package.checksums.display());
    Ok(())
}

fn print_plan(plan: &BuildPlan) {
    println!("profile: {}", plan.profile);
    println!("profile-version: {}", plan.profile_version);
    println!("project: {}", plan.project_directory.display());
    println!("output: {}", plan.output_directory.display());
    println!("theme: {}", plan.theme.as_deref().unwrap_or("none"));
    print!("command: {}", plan.program);
    for argument in &plan.arguments {
        print!(" {}", quote_argument(argument));
    }
    println!();
    println!("artifacts:");
    for artifact in &plan.artifacts {
        println!("  - {}", artifact.display());
    }
}

fn quote_argument(argument: &str) -> String {
    format!(
        "\"{}\"",
        argument.replace('\\', "\\\\").replace('"', "\\\"")
    )
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
    if let Some(execution) = &manifest.execution {
        println!("execution-program: {}", execution.program);
        println!(
            "execution-requirements: {}",
            execution
                .requirements
                .iter()
                .map(requirement_label)
                .collect::<Vec<_>>()
                .join(", ")
        );
        println!("execution-artifacts:");
        for artifact in &execution.artifacts {
            println!("  - {}", artifact.display());
        }
    }
}

fn requirement_label(requirement: &beacon::ToolRequirement) -> String {
    let mut label = requirement.command.clone();
    for alternative in &requirement.alternatives {
        label.push('|');
        label.push_str(alternative);
    }
    label
}
