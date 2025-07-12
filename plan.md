# Axis Repository Migration Plan: Legacy to Modern Package Reference Format

## Overview
This plan outlines the steps to convert the Axis repository from legacy `packages.config` format to modern SDK-style `PackageReference` format. The repository contains 61 projects, with 4 already using modern format and 57 requiring conversion.

## Current State Analysis

### Project Inventory
- **Total Projects**: 61
- **Already Modern (SDK-style)**: 4 projects
  - `/Tools/Axis.Cli/Axis.Cli.Core/Axis.Cli.Core.csproj`
  - `/Tools/Axis.Cli/Axis.Cli/Axis.Cli.csproj`
  - `/Shared/DevOps.Core.Entities/DevOps.Core.Entities.csproj`
  - `/Shared/DevOps.Core.Entities/Framework.DevOps.Core.Entities.csproj`
- **Legacy Format**: 57 projects requiring conversion

### Target Framework Analysis
- Most projects target **.NET Framework 4.8**
- Some projects target **.NET Standard 2.1** (already modern)
- Legacy projects use `ToolsVersion="15.0"` and old-style MSBuild format

### Dependency Complexity
- Heavy use of **AWS SDK packages** (multiple versions)
- **Entity Framework 6.4.4** with build props/targets
- **AutoMapper, Autofac, NLog** and other common libraries
- **Custom MYOB packages** from local NuGet feed
- **Mixed package versions** across projects

## Migration Strategy

### Phase 1: Preparation and Setup
1. **Create Git Worktree**
   ```bash
   git worktree add trees/package-reference-migration
   cd trees/package-reference-migration
   ```

2. **Backup Current State**
   - Create branch: `feature/package-reference-migration`
   - Document current package versions across all projects
   - Identify version conflicts and consolidation opportunities

3. **Analysis and Inventory**
   - Generate complete package inventory with versions
   - Identify transitive dependencies
   - Map project interdependencies
   - Document custom build targets and props

### Phase 2: Dependency Consolidation
1. **Version Alignment (Critical)**
   - **Standardize AWS SDK versions** across all projects (currently mixed versions)
   - **Align common package versions** (Newtonsoft.Json, NLog, AutoMapper, etc.)
   - **Resolve version conflicts** - ensure exact same versions across all projects
   - **Document version decisions** for future reference

2. **Create Directory.Packages.props**
   - Implement Central Package Management
   - Define all package versions centrally with **exact version matching**
   - Enable `<ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>`
   - Ensure **no version drift** between projects

### Phase 3: Project Conversion (Batch Processing)
Convert projects in dependency order (leaf projects first):

#### Batch 1: Shared Libraries (No dependencies on other projects)
- `DevOps.Entities`
- `DevOps.Shared`
- `DevOps.Logging`
- `DevOps.Security`
- `DevOps.LoggingExtensions`
- `DevOps.MvcShared`

#### Batch 2: Data Layer
- `DevOps.Data`

#### Batch 3: Business Layer
- `DevOps.Business`
- `DevOps.AWS2`
- `DevOps.IIS`
- `DevOps.DB`
- `DevOps.Operation`
- `DevOps.AcumaticaWebServices`
- `DevOps.PSS.Integration`
- `DevOps.Integration.SqlExecution`

#### Batch 4: Services
- `DevOps.Worker`
- `DevOps.JobServices`
- `DevOps.Services.Standalone`

#### Batch 5: Presentation Layer
- `DevOps.RESTFul`
- `DevOps.WCFServices`
- `DevOps.ControlPanel`
- `DevOps.LicensingRepo`

#### Batch 6: Test Projects
- All test projects (25+ projects)

#### Batch 7: Tools and Utilities
- Installer projects
- Remaining utility projects

### Phase 4: Conversion Process per Project

For each project:

1. **Pre-conversion Analysis**
   ```bash
   # Document current packages
   cat packages.config > backup_packages.config
   # Note any custom MSBuild targets
   grep -n "Import Project" *.csproj
   ```

2. **Convert Project File**
   - Change to SDK-style format: `<Project Sdk="Microsoft.NET.Sdk">`
   - Update TargetFramework: `<TargetFramework>net48</TargetFramework>`
   - Remove unnecessary MSBuild boilerplate
   - Convert `<Reference>` to `<PackageReference>`
   - Preserve project references
   - Handle special cases (Entity Framework, custom targets)

3. **Handle Special Dependencies**
   - **Entity Framework**: Ensure EF targets are preserved
   - **Custom MYOB packages**: Verify local feed accessibility
   - **Build props/targets**: Convert Import statements appropriately
   - **Assembly references**: Convert to PackageReference where possible

4. **Validation Steps**
   ```bash
   # Restore packages (NuGet restore for .NET Framework)
   nuget restore
   # Build will be validated via TeamCity pipeline after push
   # Local validation limited to project file syntax checking
   ```

### Phase 5: Solution-Level Updates

1. **Update Solution File**
   - Verify all project references are correct
   - Update any solution-level configurations

2. **Update Build Scripts**
   - Modify any build automation scripts
   - Update CI/CD pipeline configurations
   - Update Docker files if they reference packages folder

3. **Clean Up**
   - Remove `packages/` folders
   - Remove `packages.config` files
   - Update `.gitignore` to exclude new restore artifacts
   - Remove NuGet.Config entries for packages folder

### Phase 6: Testing and Validation

1. **Build Verification via TeamCity**
   ```bash
   # Push worktree branch to trigger TeamCity build
   git push origin feature/package-reference-migration
   # Monitor TeamCity pipeline for build success
   # Address any build failures through pipeline feedback
   ```

2. **Functionality Testing**
   - TeamCity will run all unit tests
   - TeamCity will run integration tests
   - Monitor pipeline results for test failures
   - Verify application deployment through pipeline

3. **Package Verification**
   - Verify all packages are restored correctly via TeamCity logs
   - Check for missing dependencies in build output
   - Validate version consistency through build artifacts

## Risk Mitigation

### High-Risk Areas
1. **Entity Framework Integration**
   - EF 6.x has specific build targets that must be preserved
   - Database migrations and model generation

2. **Custom MYOB Packages**
   - Ensure local NuGet feed is accessible
   - Verify package versions are available

3. **AWS SDK Dependencies**
   - Multiple AWS packages with potential version conflicts
   - Analyzer packages need special handling

4. **Build Automation**
   - Existing build scripts may break
   - CI/CD pipelines need updates

### Mitigation Strategies
1. **Incremental Approach**: Convert in small batches
2. **Automated Testing**: Run full test suite after each batch
3. **Rollback Plan**: Keep original branch for quick rollback
4. **Documentation**: Document all changes and issues encountered

## Success Criteria

1. **All 57 legacy projects converted** to PackageReference format
2. **TeamCity pipeline builds successfully** with MSBuild
3. **All tests pass** in TeamCity pipeline without modification
4. **Package restore works** without packages folder (validated via TeamCity)
5. **Central package management** implemented with consistent versions
6. **Build time improved** (expected benefit, measured via TeamCity)
7. **No functionality regression** (validated through TeamCity deployment)
8. **Exact version consistency** across all projects

## Timeline Estimate

- **Phase 1 (Preparation)**: 1-2 days
- **Phase 2 (Consolidation)**: 2-3 days  
- **Phase 3-4 (Conversion)**: 5-7 days (depending on complexity)
- **Phase 5 (Solution Updates)**: 1 day
- **Phase 6 (Testing)**: 2-3 days
- **Total Estimated Time**: 11-16 days

## Questions for Clarification

1. **Build Environment**: Are there any specific build server configurations that need to be considered?

2. **Package Sources**: Are all required packages available in the configured NuGet sources?

3. **Version Constraints**: Are there any specific version constraints for critical packages (AWS SDK, Entity Framework)?

4. **Testing Strategy**: What is the preferred testing approach during migration (automated vs manual)?

5. **Deployment Impact**: Will this change affect deployment processes or package deployment in TeamCity?

## Timeline Estimate

- **Phase 1 (Preparation)**: 1-2 days
- **Phase 2 (Consolidation)**: 2-3 days (critical for version consistency)
- **Phase 3-4 (Conversion)**: 5-7 days (depending on complexity)
- **Phase 5 (Solution Updates)**: 1 day
- **Phase 6 (TeamCity Validation)**: 2-3 days (including pipeline iterations)
- **Total Estimated Time**: 11-16 days

## Next Steps

1. **Review and approve this plan**
2. **Set up the worktree environment**
3. **Begin with Phase 1 preparation**
4. **Start with a small batch conversion to validate the process**

---

*This plan assumes familiarity with .NET project migration and MSBuild. Adjustments may be needed based on specific project complexities discovered during implementation.*
