# Central Package Management Migration - Hybrid Guide

## Quick Start (Experienced Developers)

### TL;DR - 30 Minute Migration
```bash
# 1. Create Directory.Packages.props
cat > Directory.Packages.props << 'EOF'
<Project>
  <PropertyGroup>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
  </PropertyGroup>
  <ItemGroup>
    <!-- Versions will be populated here -->
  </ItemGroup>
</Project>
EOF

# 2. Convert packages.config (VS: right-click project → Migrate)
# 3. Move versions to Directory.Packages.props
# 4. Fix errors in priority order: NU1103 → NU1605 → NU1202 → NU1010 → MSB4062 → NU1506
# 5. Validate: dotnet restore && dotnet build
```

### Common Fixes Reference
```xml
<!-- NU1103: Use direct reference for problematic packages -->
<Reference Include="ManagedLzma"><HintPath>path\to\dll</HintPath></Reference>

<!-- NU1605: Update conflicting versions -->
<PackageVersion Include="AWSSDK.Core" Version="3.7.300.11" />

<!-- NU1202: Use framework-compatible versions -->
<PackageVersion Include="FluentAssertions" Version="5.10.3" />

<!-- MSB4062: Disable auto-generation -->
<GenerateAssemblyInfo>false</GenerateAssemblyInfo>
```

---

## Detailed Guide (New to CPM)

### What is Central Package Management?
Central Package Management (CPM) allows you to manage NuGet package versions from a single location (`Directory.Packages.props`) instead of specifying versions in each project file. This provides:
- **Consistency:** Same package versions across all projects
- **Maintainability:** Update versions in one place
- **Security:** Easier to audit and update vulnerable packages

### Migration Overview
The migration process involves three main steps:
1. **Enable CPM:** Create `Directory.Packages.props` with central version management
2. **Convert Projects:** Change from `packages.config` to `PackageReference` format
3. **Resolve Issues:** Fix compatibility and configuration problems

### Step-by-Step Process

#### Step 1: Preparation (15 minutes)
```bash
# Create feature branch
git checkout -b feature/central-package-management

# Verify current build state
dotnet restore && dotnet build
```

#### Step 2: Enable Central Package Management (5 minutes)
Create `Directory.Packages.props` in your solution root:
```xml
<Project>
  <PropertyGroup>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
  </PropertyGroup>
  <ItemGroup>
    <!-- Package versions will be defined here -->
  </ItemGroup>
</Project>
```

#### Step 3: Convert Project Files (30-60 minutes)
For each project with `packages.config`:
1. **Visual Studio Method:** Right-click project → "Migrate packages.config to PackageReference"
2. **Manual Method:** Convert each package entry:
   ```xml
   <!-- From packages.config -->
   <package id="Newtonsoft.Json" version="13.0.1" targetFramework="net48" />
   
   <!-- To PackageReference in .csproj -->
   <PackageReference Include="Newtonsoft.Json" Version="13.0.1" />
   ```

#### Step 4: Centralize Versions (15 minutes)
Move all `Version` attributes from project files to `Directory.Packages.props`:
```xml
<!-- In Directory.Packages.props -->
<PackageVersion Include="Newtonsoft.Json" Version="13.0.1" />

<!-- In project files (remove Version attribute) -->
<PackageReference Include="Newtonsoft.Json" />
```

#### Step 5: Build and Fix Errors (2-4 hours)
```bash
dotnet restore
dotnet build 2>&1 | tee build-errors.log
```

Fix errors in this priority order:
1. **NU1103** - Package not found
2. **NU1605** - Package downgrade
3. **NU1202** - Compatibility issues
4. **NU1010** - Missing versions
5. **MSB4062** - Duplicate attributes
6. **NU1506** - Duplicate versions

---

## Error Resolution Guide

### NU1103: Unable to find package
**Quick Fix:** Use direct assembly reference for problematic packages
```xml
<Reference Include="ManagedLzma">
  <HintPath>..\..\packages\ManagedLzma.0.2.0-alpha-6\lib\net20\ManagedLzma.dll</HintPath>
</Reference>
```

**When to Use:** Pre-release packages, custom assemblies, packages not in standard feeds

### NU1605: Detected package downgrade
**Quick Fix:** Update to higher compatible version
```xml
<PackageVersion Include="AWSSDK.Core" Version="3.7.300.11" />
<PackageVersion Include="ZstdSharp.Port" Version="0.8.0" />
```

**Root Cause:** Transitive dependencies require higher versions than specified

### NU1202: Package not compatible with framework
**Quick Fix:** Use framework-compatible version
```xml
<!-- For .NET Framework 4.8 projects -->
<PackageVersion Include="FluentAssertions" Version="5.10.3" />
```

**Root Cause:** Package doesn't support your target framework

### NU1010: Package reference without version
**Quick Fix:** Add missing PackageVersion entries
```xml
<PackageVersion Include="Castle.Core" Version="4.4.0" />
<PackageVersion Include="System.Diagnostics.DiagnosticSource" Version="4.7.1" />
```

**Root Cause:** PackageReference exists but no corresponding PackageVersion

### MSB4062: Duplicate assembly attributes
**Quick Fix:** Disable auto-generation
```xml
<PropertyGroup>
  <GenerateAssemblyInfo>false</GenerateAssemblyInfo>
</PropertyGroup>
```

**Root Cause:** Conflicts with SharedAssemblyInfo.cs

### NU1506: Duplicate package version
**Quick Fix:** Remove duplicate entries from Directory.Packages.props
```bash
# Find duplicates
sort Directory.Packages.props | uniq -d
```

---

## Advanced Topics

### Package Organization Strategy
```xml
<Project>
  <PropertyGroup>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
  </PropertyGroup>
  
  <!-- Group by category for maintainability -->
  <ItemGroup Label="AWS SDK">
    <PackageVersion Include="AWSSDK.Core" Version="3.7.300.11" />
    <PackageVersion Include="AWSSDK.CloudFormation" Version="3.7.300.11" />
  </ItemGroup>
  
  <ItemGroup Label="Testing">
    <PackageVersion Include="FluentAssertions" Version="5.10.3" />
    <PackageVersion Include="Castle.Core" Version="4.4.0" />
  </ItemGroup>
</Project>
```

### Build System Integration
**TeamCity Requirements:**
- NuGet 5.4.0+ for CPM support
- Clear package cache between builds
- Update build templates for CPM

**Local Development:**
```bash
# Recommended validation sequence
dotnet clean
dotnet nuget locals all --clear
dotnet restore
dotnet build --configuration Release
```

### Troubleshooting Tips
1. **Build fails immediately:** Check Directory.Packages.props syntax
2. **Specific packages fail:** Consider direct assembly references
3. **Performance issues:** Clear NuGet cache
4. **Version conflicts:** Use dependency graph to understand requirements

---

## Success Validation

### Completion Checklist
- [ ] All projects build successfully
- [ ] No NU1103, NU1605, NU1202, NU1010 errors
- [ ] TeamCity builds pass
- [ ] Package versions are secure and up-to-date
- [ ] Directory.Packages.props is well-organized

### Metrics to Track
- **Error Count:** Monitor reduction in specific error codes
- **Build Success Rate:** Maintain or improve build reliability
- **Package Count:** Optimize number of unique package versions
- **Security:** Reduce vulnerable package count

---

## Next Steps

### Immediate Actions
1. Complete any remaining non-blocking warnings
2. Update team documentation
3. Share learnings with other teams

### Long-term Maintenance
1. Set up automated package update processes
2. Implement security vulnerability monitoring
3. Establish package update review procedures
4. Create templates for new projects

---

## Need Help?

### Common Issues
- **Migration taking too long?** Focus on blocking errors first, warnings can wait
- **Specific package problems?** Check the detailed error reference guide
- **Build system issues?** Verify NuGet version and cache configuration
- **Team coordination?** Use incremental commits and clear communication

### Resources
- [Detailed Error Reference](../knowledge-base/error-reference.md)
- [Best Practices Guide](../knowledge-base/best-practices.md)
- [Step-by-Step Runbook](../runbook/migration-runbook.md)
- [Comprehensive Guide](../structured-guide/migration-plan.md)
