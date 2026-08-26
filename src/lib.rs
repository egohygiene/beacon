// Copyright 2026 Ego Hygiene
// SPDX-License-Identifier: MIT

//! Beacon's profile registry, project initialization, and publication execution core.

use anyhow::{Context, Result, bail};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::ffi::OsStr;
use std::fs::{self, File};
use std::io::{BufReader, Read, Write};
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
    pub execution: Option<ExecutionContract>,
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

#[derive(Debug, Deserialize)]
pub struct ExecutionContract {
    pub program: String,
    pub arguments: Vec<String>,
    pub default_output: PathBuf,
    #[serde(default)]
    pub default_theme: Option<String>,
    #[serde(default)]
    pub theme_values: BTreeMap<String, String>,
    pub requirements: Vec<ToolRequirement>,
    pub artifacts: Vec<PathBuf>,
}

#[derive(Debug, Deserialize)]
pub struct ToolRequirement {
    pub command: String,
    #[serde(default)]
    pub alternatives: Vec<String>,
    #[serde(default = "default_version_arguments")]
    pub version_arguments: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct ProjectManifest {
    beacon: ProjectEnvelope,
    provenance: Option<ProjectProvenance>,
}

#[derive(Debug, Deserialize)]
struct ProjectEnvelope {
    schema_version: u32,
    profile: String,
    profile_version: String,
    theme: Option<String>,
}

#[derive(Debug, Deserialize)]
struct ProjectProvenance {
    source_repository: Option<String>,
    source_revision: Option<String>,
}

#[derive(Debug)]
pub struct BuildOptions {
    pub output_directory: Option<PathBuf>,
    pub theme: Option<String>,
}

#[derive(Debug)]
pub struct BuildPlan {
    pub profile: String,
    pub profile_version: String,
    pub theme: Option<String>,
    pub project_directory: PathBuf,
    pub output_directory: PathBuf,
    pub program: String,
    pub arguments: Vec<String>,
    pub artifacts: Vec<PathBuf>,
    argument_templates: Vec<String>,
    profile_directory: PathBuf,
    theme_value: Option<String>,
    source_repository: Option<String>,
    source_revision: Option<String>,
}

#[derive(Debug)]
pub struct DoctorCheck {
    pub profile: String,
    pub command: String,
    pub available: bool,
    pub detail: String,
}

#[derive(Debug)]
pub struct PackageResult {
    pub directory: PathBuf,
    pub manifest: PathBuf,
    pub checksums: PathBuf,
    pub artifact_count: usize,
}

#[derive(Debug)]
struct ResolvedTheme {
    id: String,
    value: String,
}

#[derive(Debug, Serialize)]
struct PublicationPackageManifest {
    schema_version: u32,
    profile: String,
    profile_version: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    theme: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    source_repository: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    source_revision: Option<String>,
    artifacts: Vec<PackagedArtifact>,
}

#[derive(Debug, Serialize)]
struct PackagedArtifact {
    path: String,
    sha256: String,
    bytes: u64,
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

    pub fn doctor(
        &self,
        profile: Option<&str>,
        allow_executable_adapter: bool,
    ) -> Result<Vec<DoctorCheck>> {
        self.ensure_adapter_trust(allow_executable_adapter)?;
        let packages = if let Some(profile) = profile {
            vec![self.find(profile)?]
        } else {
            self.packages.iter().collect()
        };
        let mut checks = Vec::new();
        for package in packages {
            validate_package(package)?;
            let execution = package
                .manifest
                .execution
                .as_ref()
                .context("validated execution adapter disappeared")?;
            for requirement in &execution.requirements {
                checks.push(check_tool(&package.manifest.id, requirement));
            }
        }
        Ok(checks)
    }

    pub fn plan(&self, project: &Path, options: &BuildOptions) -> Result<BuildPlan> {
        let project_directory = project
            .canonicalize()
            .with_context(|| format!("failed to resolve project {}", project.display()))?;
        if !project_directory.is_dir() {
            bail!("project is not a directory: {}", project.display());
        }
        let project_manifest_path = project_directory.join("beacon-project.toml");
        let project_manifest: ProjectManifest = toml::from_str(
            &fs::read_to_string(&project_manifest_path).with_context(|| {
                format!(
                    "failed to read project manifest {}",
                    project_manifest_path.display()
                )
            })?,
        )
        .with_context(|| {
            format!(
                "invalid project manifest {}",
                project_manifest_path.display()
            )
        })?;
        validate_project_envelope(&project_manifest)?;

        let package = self.find(&project_manifest.beacon.profile)?;
        validate_package(package)?;
        if project_manifest.beacon.profile_version != package.manifest.version {
            bail!(
                "project pins {} {}, but the registry provides {}",
                package.manifest.id,
                project_manifest.beacon.profile_version,
                package.manifest.version
            );
        }
        let execution = package
            .manifest
            .execution
            .as_ref()
            .context("validated execution adapter disappeared")?;
        let resolved_theme = resolve_theme(
            execution,
            options.theme.as_ref(),
            project_manifest.beacon.theme.as_ref(),
            &package.manifest.id,
        )?;
        let output_directory = resolve_project_path(
            &project_directory,
            options
                .output_directory
                .as_ref()
                .unwrap_or(&execution.default_output),
        )?;
        ensure_safe_output_directory(&output_directory, &project_directory, package)?;
        let profile_directory = package.directory.canonicalize().with_context(|| {
            format!(
                "failed to resolve profile directory {}",
                package.directory.display()
            )
        })?;
        let arguments = resolve_execution_arguments(
            &execution.arguments,
            &profile_directory,
            &project_directory,
            &output_directory,
            resolved_theme.as_ref().map(|theme| theme.value.as_str()),
        )?;

        Ok(BuildPlan {
            profile: package.manifest.id.clone(),
            profile_version: package.manifest.version.clone(),
            theme: resolved_theme.as_ref().map(|theme| theme.id.clone()),
            project_directory,
            output_directory,
            program: execution.program.clone(),
            arguments,
            artifacts: execution.artifacts.clone(),
            argument_templates: execution.arguments.clone(),
            profile_directory,
            theme_value: resolved_theme.map(|theme| theme.value),
            source_repository: project_manifest
                .provenance
                .as_ref()
                .and_then(|provenance| provenance.source_repository.clone()),
            source_revision: project_manifest
                .provenance
                .as_ref()
                .and_then(|provenance| provenance.source_revision.clone()),
        })
    }

    pub fn build(&self, plan: &BuildPlan, allow_executable_adapter: bool) -> Result<()> {
        self.ensure_adapter_trust(allow_executable_adapter)?;
        execute_build(plan)
    }

    pub fn package(
        &self,
        plan: &BuildPlan,
        package_directory: Option<&Path>,
        allow_executable_adapter: bool,
    ) -> Result<PackageResult> {
        let destination = if let Some(destination) = package_directory {
            resolve_project_path(&plan.project_directory, destination)?
        } else {
            resolve_project_path(
                &plan.project_directory,
                &PathBuf::from("dist").join(format!("{}-{}", plan.profile, plan.profile_version)),
            )?
        };
        ensure_safe_package_directory(&destination, plan)?;
        self.build(plan, allow_executable_adapter)?;
        package_artifacts(plan, &destination)
    }

    fn ensure_adapter_trust(&self, allow_executable_adapter: bool) -> Result<()> {
        if !self.is_builtin() && !allow_executable_adapter {
            bail!(
                "refusing to execute an adapter from an external registry; inspect it first and pass --allow-executable-adapter"
            );
        }
        Ok(())
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
    validate_initializer(package)?;
    validate_execution(package)
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

fn validate_execution(package: &TemplatePackage) -> Result<()> {
    let manifest = &package.manifest;
    let execution = manifest
        .execution
        .as_ref()
        .with_context(|| format!("template {} declares no execution adapter", manifest.id))?;
    validate_execution_command(execution, &manifest.id)?;
    validate_execution_requirements(execution, &manifest.id)?;
    validate_execution_artifacts(execution, &manifest.id)?;
    validate_execution_themes(execution, &manifest.id)
}

fn validate_execution_command(execution: &ExecutionContract, profile: &str) -> Result<()> {
    if execution.program.trim().is_empty()
        || execution.program.contains(char::is_whitespace)
        || Path::new(&execution.program).components().count() != 1
    {
        bail!("template {profile} execution program must be a bare command name");
    }
    if execution.arguments.is_empty() {
        bail!("template {profile} declares no execution arguments");
    }
    validate_relative_path(
        &execution.default_output,
        "default execution output",
        profile,
    )?;
    let allowed_tokens = ["{{profile}}", "{{project}}", "{{output}}", "{{theme}}"];
    let mut has_output_token = false;
    for argument in &execution.arguments {
        if argument.trim().is_empty() {
            bail!("template {profile} has an empty execution argument");
        }
        has_output_token |= argument.contains("{{output}}");
        let mut remainder = argument.as_str();
        while let Some(start) = remainder.find("{{") {
            let token_tail = &remainder[start..];
            let end = token_tail.find("}}").with_context(|| {
                format!("template {profile} has an unterminated execution token")
            })?;
            let token = &token_tail[..end + 2];
            if !allowed_tokens.contains(&token) {
                bail!("template {profile} has unsupported execution token {token}");
            }
            remainder = &token_tail[end + 2..];
        }
    }
    if !has_output_token {
        bail!("template {profile} execution arguments must contain {{{{output}}}}");
    }
    Ok(())
}

fn validate_execution_requirements(execution: &ExecutionContract, profile: &str) -> Result<()> {
    if execution.requirements.is_empty() {
        bail!("template {profile} declares no execution requirements");
    }
    let mut requirement_names = BTreeSet::new();
    for requirement in &execution.requirements {
        let mut commands = vec![&requirement.command];
        for alternative in &requirement.alternatives {
            commands.push(alternative);
        }
        for command in commands {
            if command.trim().is_empty()
                || command.contains(char::is_whitespace)
                || Path::new(command).components().count() != 1
            {
                bail!("template {profile} has an invalid required command");
            }
            if !requirement_names.insert(command.as_str()) {
                bail!("template {profile} repeats required command {command}");
            }
        }
    }
    if !requirement_names.contains(execution.program.as_str()) {
        bail!(
            "template {profile} execution requirements must include program {}",
            execution.program
        );
    }
    Ok(())
}

fn validate_execution_artifacts(execution: &ExecutionContract, profile: &str) -> Result<()> {
    if execution.artifacts.is_empty() {
        bail!("template {profile} declares no packaged artifacts");
    }
    let mut artifact_paths = BTreeSet::new();
    for artifact in &execution.artifacts {
        validate_relative_path(artifact, "packaged artifact", profile)?;
        if artifact_paths.iter().any(|existing: &&PathBuf| {
            artifact.starts_with(existing) || existing.starts_with(artifact)
        }) {
            bail!(
                "template {profile} has overlapping packaged artifact {}",
                artifact.display()
            );
        }
        if !artifact_paths.insert(artifact) {
            bail!(
                "template {profile} repeats packaged artifact {}",
                artifact.display()
            );
        }
    }
    Ok(())
}

fn validate_execution_themes(execution: &ExecutionContract, profile: &str) -> Result<()> {
    if execution.theme_values.is_empty() {
        if execution.default_theme.is_some()
            || execution
                .arguments
                .iter()
                .any(|argument| argument.contains("{{theme}}"))
        {
            bail!("template {profile} uses themes without declaring execution.theme_values");
        }
    } else {
        let default_theme = execution.default_theme.as_ref().with_context(|| {
            format!("template {profile} declares theme values without a default theme")
        })?;
        if !execution.theme_values.contains_key(default_theme) {
            bail!("template {profile} default theme is not declared: {default_theme}");
        }
        if !execution
            .arguments
            .iter()
            .any(|argument| argument.contains("{{theme}}"))
        {
            bail!("template {profile} declares themes but does not pass {{{{theme}}}}");
        }
        for (theme, value) in &execution.theme_values {
            if !is_kebab_case_identifier(theme) || value.trim().is_empty() {
                bail!("template {profile} has an invalid execution theme");
            }
        }
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

fn default_version_arguments() -> Vec<String> {
    vec!["--version".to_owned()]
}

fn validate_project_envelope(project: &ProjectManifest) -> Result<()> {
    if project.beacon.schema_version != 1 {
        bail!(
            "project uses unsupported Beacon schema version {}",
            project.beacon.schema_version
        );
    }
    if !is_kebab_case_identifier(&project.beacon.profile) {
        bail!("project profile must be lowercase kebab-case");
    }
    if !is_three_part_version(&project.beacon.profile_version) {
        bail!("project profile version must use x.y.z semantic versioning");
    }
    if project
        .beacon
        .theme
        .as_ref()
        .is_some_and(|theme| theme.trim().is_empty())
    {
        bail!("project theme must not be empty");
    }
    if let Some(provenance) = &project.provenance {
        for (field, value) in [
            ("source_repository", &provenance.source_repository),
            ("source_revision", &provenance.source_revision),
        ] {
            if value.as_ref().is_some_and(|value| value.trim().is_empty()) {
                bail!("project provenance.{field} must not be empty");
            }
        }
    }
    Ok(())
}

fn resolve_theme(
    execution: &ExecutionContract,
    requested: Option<&String>,
    project_theme: Option<&String>,
    profile: &str,
) -> Result<Option<ResolvedTheme>> {
    if execution.theme_values.is_empty() {
        if requested.is_some() || project_theme.is_some() {
            bail!("profile {profile} does not support themes");
        }
        return Ok(None);
    }
    let theme = requested
        .or(project_theme)
        .or(execution.default_theme.as_ref())
        .context("validated default theme disappeared")?;
    let value = execution.theme_values.get(theme).with_context(|| {
        format!(
            "profile {profile} does not support theme {theme}; available: {}",
            execution
                .theme_values
                .keys()
                .cloned()
                .collect::<Vec<_>>()
                .join(", ")
        )
    })?;
    Ok(Some(ResolvedTheme {
        id: theme.clone(),
        value: value.clone(),
    }))
}

fn resolve_project_path(project_directory: &Path, path: &Path) -> Result<PathBuf> {
    let candidate = if path.is_absolute() {
        path.to_path_buf()
    } else {
        project_directory.join(path)
    };
    normalize_absolute_path(&candidate)
}

fn normalize_absolute_path(path: &Path) -> Result<PathBuf> {
    let absolute = if path.is_absolute() {
        path.to_path_buf()
    } else {
        std::env::current_dir()
            .context("failed to resolve current directory")?
            .join(path)
    };
    let mut normalized = PathBuf::new();
    for component in absolute.components() {
        match component {
            Component::Prefix(prefix) => normalized.push(prefix.as_os_str()),
            Component::RootDir => normalized.push(Path::new("/")),
            Component::CurDir => {}
            Component::ParentDir => {
                if !normalized.pop() {
                    bail!("path escapes the filesystem root: {}", path.display());
                }
            }
            Component::Normal(value) => normalized.push(value),
        }
    }
    if normalized.exists() && fs::symlink_metadata(&normalized)?.file_type().is_symlink() {
        bail!("refusing symbolic-link path: {}", normalized.display());
    }
    canonicalize_existing_prefix(&normalized)
}

fn canonicalize_existing_prefix(path: &Path) -> Result<PathBuf> {
    let mut existing = path.to_path_buf();
    let mut missing = Vec::new();
    while !existing.exists() {
        let name = existing.file_name().with_context(|| {
            format!("path has no existing filesystem prefix: {}", path.display())
        })?;
        missing.push(name.to_os_string());
        existing.pop();
    }
    let mut resolved = existing
        .canonicalize()
        .with_context(|| format!("failed to resolve path prefix {}", existing.display()))?;
    for component in missing.iter().rev() {
        resolved.push(component);
    }
    Ok(resolved)
}

fn ensure_safe_output_directory(
    output: &Path,
    project: &Path,
    package: &TemplatePackage,
) -> Result<()> {
    if output.parent().is_none()
        || output == Path::new("/")
        || paths_refer_to_same_location(output, project)
        || project.starts_with(output)
        || output.starts_with(&package.directory)
        || package.directory.starts_with(output)
        || paths_refer_to_same_location(output, Path::new(env!("CARGO_MANIFEST_DIR")))
    {
        bail!("refusing unsafe build output: {}", output.display());
    }
    if output.exists() {
        let metadata = fs::symlink_metadata(output)
            .with_context(|| format!("failed to inspect build output {}", output.display()))?;
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            bail!(
                "build output must be a directory and not a symbolic link: {}",
                output.display()
            );
        }
    }
    Ok(())
}

fn resolve_execution_arguments(
    templates: &[String],
    profile: &Path,
    project: &Path,
    output: &Path,
    theme: Option<&str>,
) -> Result<Vec<String>> {
    let replacements = [
        ("{{profile}}", profile.display().to_string()),
        ("{{project}}", project.display().to_string()),
        ("{{output}}", output.display().to_string()),
        ("{{theme}}", theme.unwrap_or_default().to_owned()),
    ];
    templates
        .iter()
        .map(|template| {
            let mut argument = template.clone();
            for (token, value) in &replacements {
                argument = argument.replace(token, value);
            }
            if argument.contains("{{") {
                bail!("unresolved execution token in {argument}");
            }
            Ok(argument)
        })
        .collect()
}

fn check_tool(profile: &str, requirement: &ToolRequirement) -> DoctorCheck {
    let mut command_label = requirement.command.clone();
    let mut commands = vec![&requirement.command];
    for alternative in &requirement.alternatives {
        command_label.push('|');
        command_label.push_str(alternative);
        commands.push(alternative);
    }
    let mut errors = Vec::new();
    for command in commands {
        match Command::new(command)
            .args(&requirement.version_arguments)
            .output()
        {
            Ok(output) => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let stderr = String::from_utf8_lossy(&output.stderr);
                let detail = stdout
                    .lines()
                    .chain(stderr.lines())
                    .find(|line| !line.trim().is_empty())
                    .unwrap_or("available")
                    .trim()
                    .to_owned();
                return DoctorCheck {
                    profile: profile.to_owned(),
                    command: command_label,
                    available: true,
                    detail: format!("{command}: {detail}"),
                };
            }
            Err(error) => errors.push(format!("{command}: {error}")),
        }
    }
    DoctorCheck {
        profile: profile.to_owned(),
        command: command_label,
        available: false,
        detail: errors.join("; "),
    }
}

fn execute_build(plan: &BuildPlan) -> Result<()> {
    ensure_replaceable_output(&plan.output_directory)?;
    let parent = plan.output_directory.parent().with_context(|| {
        format!(
            "build output must have a writable parent: {}",
            plan.output_directory.display()
        )
    })?;
    fs::create_dir_all(parent)
        .with_context(|| format!("failed to create build parent {}", parent.display()))?;
    let temporary = tempfile::Builder::new()
        .prefix(".beacon-build-")
        .tempdir_in(parent)
        .with_context(|| format!("failed to create temporary build in {}", parent.display()))?;
    let staged_output = temporary.path().join("output");
    let arguments = resolve_execution_arguments(
        &plan.argument_templates,
        &plan.profile_directory,
        &plan.project_directory,
        &staged_output,
        plan.theme_value.as_deref(),
    )?;
    let status = Command::new(&plan.program)
        .args(&arguments)
        .current_dir(&plan.project_directory)
        .status()
        .with_context(|| format!("failed to run build adapter {}", plan.program))?;
    if !status.success() {
        bail!("{} build adapter failed with status {status}", plan.profile);
    }
    verify_artifacts(&staged_output, &plan.artifacts)?;
    fs::write(
        staged_output.join(".beacon-output"),
        format!(
            "profile = {:?}\nprofile_version = {:?}\n",
            plan.profile, plan.profile_version
        ),
    )?;

    if plan.output_directory.exists() {
        fs::remove_dir_all(&plan.output_directory).with_context(|| {
            format!(
                "failed to replace previous Beacon output {}",
                plan.output_directory.display()
            )
        })?;
    }
    fs::rename(&staged_output, &plan.output_directory).with_context(|| {
        format!(
            "failed to finalize build output {}",
            plan.output_directory.display()
        )
    })?;
    Ok(())
}

fn ensure_replaceable_output(output: &Path) -> Result<()> {
    if !output.exists() {
        return Ok(());
    }
    let is_empty = fs::read_dir(output)?.next().transpose()?.is_none();
    if !is_empty && !output.join(".beacon-output").is_file() {
        bail!(
            "refusing to replace unowned build output {}; choose a new --output-directory",
            output.display()
        );
    }
    Ok(())
}

fn verify_artifacts(output: &Path, artifacts: &[PathBuf]) -> Result<()> {
    let resolved_output = output
        .canonicalize()
        .with_context(|| format!("build adapter did not create output {}", output.display()))?;
    for artifact in artifacts {
        let path = output.join(artifact);
        let resolved_path = path.canonicalize().with_context(|| {
            format!("build is missing required artifact {}", artifact.display())
        })?;
        if !resolved_path.starts_with(&resolved_output) {
            bail!("artifact escapes build output: {}", artifact.display());
        }
        let metadata = fs::symlink_metadata(&path).with_context(|| {
            format!("build is missing required artifact {}", artifact.display())
        })?;
        if metadata.file_type().is_symlink()
            || (metadata.is_file() && metadata.len() == 0)
            || (!metadata.is_file() && !metadata.is_dir())
        {
            bail!("invalid required artifact: {}", artifact.display());
        }
    }
    Ok(())
}

fn package_artifacts(plan: &BuildPlan, destination: &Path) -> Result<PackageResult> {
    ensure_safe_package_directory(destination, plan)?;
    let parent = destination.parent().with_context(|| {
        format!(
            "package destination must have a writable parent: {}",
            destination.display()
        )
    })?;
    fs::create_dir_all(parent)
        .with_context(|| format!("failed to create package parent {}", parent.display()))?;
    let temporary = tempfile::Builder::new()
        .prefix(".beacon-package-")
        .tempdir_in(parent)
        .with_context(|| format!("failed to stage package in {}", parent.display()))?;
    let bundle = temporary.path().join("bundle");
    let artifact_root = bundle.join("artifacts");
    fs::create_dir_all(&artifact_root)?;
    for artifact in &plan.artifacts {
        copy_artifact(
            &plan.output_directory.join(artifact),
            &artifact_root.join(artifact),
        )?;
    }
    let mut packaged_files = collect_files(&artifact_root)?;
    packaged_files.sort();
    let mut artifacts = Vec::new();
    let mut checksum_lines = Vec::new();
    for path in packaged_files {
        let relative = path
            .strip_prefix(&bundle)
            .context("packaged artifact escaped bundle")?;
        let digest = sha256_file(&path)?;
        let bytes = path.metadata()?.len();
        if bytes == 0 {
            bail!("refusing empty packaged artifact: {}", path.display());
        }
        let relative_text = path_to_portable_string(relative)?;
        checksum_lines.push(format!("{digest}  {relative_text}"));
        artifacts.push(PackagedArtifact {
            path: relative_text,
            sha256: digest,
            bytes,
        });
    }
    let manifest_data = PublicationPackageManifest {
        schema_version: 1,
        profile: plan.profile.clone(),
        profile_version: plan.profile_version.clone(),
        theme: plan.theme.clone(),
        source_repository: plan.source_repository.clone(),
        source_revision: plan.source_revision.clone(),
        artifacts,
    };
    let manifest_path = bundle.join("beacon-package.json");
    let mut manifest_file = File::create(&manifest_path)?;
    serde_json::to_writer_pretty(&mut manifest_file, &manifest_data)?;
    manifest_file.write_all(b"\n")?;
    let checksums_path = bundle.join("SHA256SUMS");
    fs::write(&checksums_path, checksum_lines.join("\n") + "\n")?;

    if destination.exists() {
        fs::remove_dir(destination)?;
    }
    fs::rename(&bundle, destination)
        .with_context(|| format!("failed to finalize package at {}", destination.display()))?;
    Ok(PackageResult {
        directory: destination.to_path_buf(),
        manifest: destination.join("beacon-package.json"),
        checksums: destination.join("SHA256SUMS"),
        artifact_count: manifest_data.artifacts.len(),
    })
}

fn ensure_safe_package_directory(destination: &Path, plan: &BuildPlan) -> Result<()> {
    if destination.parent().is_none()
        || destination == Path::new("/")
        || paths_refer_to_same_location(destination, &plan.project_directory)
        || plan.project_directory.starts_with(destination)
        || paths_refer_to_same_location(destination, &plan.output_directory)
        || plan.output_directory.starts_with(destination)
        || destination.starts_with(&plan.output_directory)
        || destination.starts_with(&plan.profile_directory)
        || plan.profile_directory.starts_with(destination)
    {
        bail!(
            "refusing unsafe package destination: {}",
            destination.display()
        );
    }
    if destination.exists() {
        let metadata = fs::symlink_metadata(destination).with_context(|| {
            format!(
                "failed to inspect package destination {}",
                destination.display()
            )
        })?;
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            bail!(
                "package destination must be a directory and not a symbolic link: {}",
                destination.display()
            );
        }
        if fs::read_dir(destination)?.next().transpose()?.is_some() {
            bail!(
                "package destination is not empty: {}",
                destination.display()
            );
        }
    }
    Ok(())
}

fn copy_artifact(source: &Path, destination: &Path) -> Result<()> {
    let metadata = fs::symlink_metadata(source)
        .with_context(|| format!("failed to inspect artifact {}", source.display()))?;
    if metadata.file_type().is_symlink() {
        bail!("refusing symbolic-link artifact: {}", source.display());
    }
    if metadata.is_dir() {
        fs::create_dir_all(destination)?;
        let mut entries = fs::read_dir(source)?.collect::<std::io::Result<Vec<_>>>()?;
        entries.sort_by_key(std::fs::DirEntry::file_name);
        for entry in entries {
            copy_artifact(&entry.path(), &destination.join(entry.file_name()))?;
        }
    } else if metadata.is_file() {
        if let Some(parent) = destination.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::copy(source, destination)?;
    } else {
        bail!("unsupported artifact type: {}", source.display());
    }
    Ok(())
}

fn collect_files(root: &Path) -> Result<Vec<PathBuf>> {
    let mut files = Vec::new();
    for entry in fs::read_dir(root)? {
        let path = entry?.path();
        let metadata = fs::symlink_metadata(&path)?;
        if metadata.file_type().is_symlink() {
            bail!("refusing symbolic-link artifact: {}", path.display());
        }
        if metadata.is_dir() {
            files.extend(collect_files(&path)?);
        } else if metadata.is_file() {
            files.push(path);
        }
    }
    Ok(files)
}

fn sha256_file(path: &Path) -> Result<String> {
    let mut reader = BufReader::new(File::open(path)?);
    let mut digest = Sha256::new();
    let mut buffer = vec![0_u8; 64 * 1024];
    loop {
        let count = reader.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        digest.update(&buffer[..count]);
    }
    Ok(format!("{:x}", digest.finalize()))
}

fn path_to_portable_string(path: &Path) -> Result<String> {
    let parts = path
        .components()
        .map(|component| match component {
            Component::Normal(value) => value
                .to_str()
                .map(str::to_owned)
                .context("artifact path is not valid UTF-8"),
            _ => bail!("artifact path is not relative: {}", path.display()),
        })
        .collect::<Result<Vec<_>>>()?;
    Ok(parts.join("/"))
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
            directory.join("scripts/build.py"),
            r#"import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
output = Path(args.output)
output.mkdir(parents=True)
(output / "fixture.pdf").write_bytes(b"fixture artifact")
(output / "nested").mkdir()
(output / "nested" / "z.txt").write_text("z", encoding="utf-8")
(output / "nested" / "a.txt").write_text("a", encoding="utf-8")
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

[execution]
program = "python3"
arguments = ["{{{{profile}}}}/scripts/build.py", "--project={{{{project}}}}", "--output={{{{output}}}}"]
default_output = "build"
artifacts = ["fixture.pdf", "nested"]

[[execution.requirements]]
command = "python3"
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

    #[test]
    fn plans_builds_and_packages_a_pinned_project() {
        let root = TempDir::new().unwrap();
        write_fixture(root.path(), "fixture");
        let registry = Registry::discover(root.path()).unwrap();
        let project = root.path().join("project");
        let options = InitializationOptions {
            title: "Package Fixture".into(),
            author: "Beacon Maintainers".into(),
            publisher: None,
            edition: "1".into(),
            project_id: None,
            theme: None,
            python: PathBuf::from("python3"),
        };
        registry
            .initialize("fixture", &project, &options, true)
            .unwrap();
        let plan = registry
            .plan(
                &project,
                &BuildOptions {
                    output_directory: None,
                    theme: None,
                },
            )
            .unwrap();
        assert_eq!(plan.profile, "fixture");
        assert!(
            plan.arguments
                .iter()
                .any(|argument| argument.contains("build"))
        );

        let error = registry.build(&plan, false).unwrap_err();
        assert!(error.to_string().contains("external registry"));
        registry.build(&plan, true).unwrap();
        assert!(plan.output_directory.join("fixture.pdf").is_file());

        let package = registry.package(&plan, None, true).unwrap();
        assert_eq!(package.artifact_count, 3);
        assert!(package.manifest.is_file());
        let checksums = fs::read_to_string(package.checksums).unwrap();
        let paths = checksums
            .lines()
            .map(|line| line.split_once("  ").unwrap().1)
            .collect::<Vec<_>>();
        assert_eq!(
            paths,
            [
                "artifacts/fixture.pdf",
                "artifacts/nested/a.txt",
                "artifacts/nested/z.txt"
            ]
        );
        let first_manifest = fs::read_to_string(package.manifest).unwrap();
        let second_package = registry
            .package(&plan, Some(Path::new("dist/second")), true)
            .unwrap();
        assert_eq!(
            first_manifest,
            fs::read_to_string(second_package.manifest).unwrap()
        );
        assert_eq!(
            checksums,
            fs::read_to_string(second_package.checksums).unwrap()
        );
    }

    #[test]
    fn fails_a_build_that_does_not_produce_declared_artifacts() {
        let root = TempDir::new().unwrap();
        write_fixture(root.path(), "fixture");
        let registry = Registry::discover(root.path()).unwrap();
        let project = root.path().join("project");
        let options = InitializationOptions {
            title: "Broken Fixture".into(),
            author: "Beacon Maintainers".into(),
            publisher: None,
            edition: "1".into(),
            project_id: None,
            theme: None,
            python: PathBuf::from("python3"),
        };
        registry
            .initialize("fixture", &project, &options, true)
            .unwrap();
        fs::write(
            root.path().join("fixture/scripts/build.py"),
            "import pathlib, sys\npathlib.Path(sys.argv[-1].split('=', 1)[1]).mkdir(parents=True)\n",
        )
        .unwrap();
        let plan = registry
            .plan(
                &project,
                &BuildOptions {
                    output_directory: None,
                    theme: None,
                },
            )
            .unwrap();
        let error = registry.build(&plan, true).unwrap_err();
        assert!(error.to_string().contains("missing required artifact"));
        assert!(!plan.output_directory.exists());
    }

    #[test]
    fn doctor_accepts_a_declared_tool_alternative() {
        let root = TempDir::new().unwrap();
        write_fixture(root.path(), "fixture");
        let manifest_path = root.path().join("fixture/beacon-template.toml");
        let manifest = fs::read_to_string(&manifest_path).unwrap().replace(
            "command = \"python3\"",
            "command = \"beacon-command-that-does-not-exist\"\nalternatives = [\"python3\"]",
        );
        fs::write(manifest_path, manifest).unwrap();
        let registry = Registry::discover(root.path()).unwrap();
        let checks = registry.doctor(Some("fixture"), true).unwrap();
        assert_eq!(checks.len(), 1);
        assert!(checks[0].available);
        assert!(checks[0].command.ends_with("|python3"));
        assert!(checks[0].detail.starts_with("python3:"));
    }

    #[test]
    fn refuses_to_replace_unowned_build_output() {
        let root = TempDir::new().unwrap();
        write_fixture(root.path(), "fixture");
        let registry = Registry::discover(root.path()).unwrap();
        let project = root.path().join("project");
        let options = InitializationOptions {
            title: "Protected Fixture".into(),
            author: "Beacon Maintainers".into(),
            publisher: None,
            edition: "1".into(),
            project_id: None,
            theme: None,
            python: PathBuf::from("python3"),
        };
        registry
            .initialize("fixture", &project, &options, true)
            .unwrap();
        let output = project.join("build");
        fs::create_dir(&output).unwrap();
        fs::write(output.join("keep.txt"), "do not replace").unwrap();
        let plan = registry
            .plan(
                &project,
                &BuildOptions {
                    output_directory: None,
                    theme: None,
                },
            )
            .unwrap();
        let error = registry.build(&plan, true).unwrap_err();
        assert!(error.to_string().contains("unowned build output"));
        assert_eq!(
            fs::read_to_string(output.join("keep.txt")).unwrap(),
            "do not replace"
        );
    }
}
