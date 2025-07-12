# Central Package Management Migration Runbook

## Prerequisites and Preparation

### Required Tools
- [ ] Visual Studio 2019+ or VS Code with C# extension
- [ ] .NET SDK 4.8+ and .NET Core 3.1+
- [ ] Git client
- [ ] Access to TeamCity build system
- [ ] NuGet CLI 5.4.0+

### Pre-Flight Checklist
- [ ] Create feature branch: `feature/central-package-management`
- [ ] Backup current solution state
- [ ] Verify all projects build successfully
- [ ] Document current package.config inventory
- [ ] Identify problematic packages (pre-release, custom assemblies)

### Environment Setup
```bash
# Clone and switch to feature branch
git checkout -b feature/central-package-management

# Verify build state
dotnet restore
dotnet build
```

## Execution Phases

### Phase 1: Initial Setup (30 minutes)

#### Step 1.1: Create Directory.Packages.props
**Location:** Solution root directory
**Action:** Create file with basic structure
```xml
<Project>
  <PropertyGroup>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
  </PropertyGroup>
  <ItemGroup>
    <!-- Package versions will be populated here -->
  </ItemGroup>
</Project>
```

#### Step 1.2: Inventory Current Packages
**Command:**
```bash
# Find all packages.config files
find . -name "packages.config" -type f

# Count total package references
grep -r "PackageReference" --include="*.csproj" . | wc -l
```

**Validation Checkpoint:** Document total project count and package references

### Phase 2: Bulk Conversion (2-4 hours)

#### Step 2.1: Convert packages.config to PackageReference
**For each project with packages.config:**
1. Right-click project in Visual Studio
2. Select "Migrate packages.config to PackageReference"
3. Review and accept changes

**Alternative - Manual conversion:**
```xml
<!-- Old packages.config entry -->
<package id="Newtonsoft.Json" version="13.0.1" targetFramework="net48" />

<!-- New PackageReference -->
<PackageReference Include="Newtonsoft.Json" />
```

#### Step 2.2: Extract Package Versions
**Action:** Move all Version attributes to Directory.Packages.props
```xml
<!-- In Directory.Packages.props -->
<PackageVersion Include="Newtonsoft.Json" Version="13.0.1" />

<!-- In project file -->
<PackageReference Include="Newtonsoft.Json" />
```

**Validation Checkpoint:** 
```bash
# Verify no Version attributes remain in project files
grep -r 'PackageReference.*Version=' --include="*.csproj" .
# Should return no results
```

### Phase 3: Error Resolution (4-8 hours)

#### Step 3.1: Build and Identify Errors
```bash
dotnet restore
dotnet build 2>&1 | tee build-log.txt
```

#### Step 3.2: Systematic Error Resolution

**Priority 1: NU1103 Errors**
```bash
# Find NU1103 errors
grep "NU1103" build-log.txt

# For each NU1103 error:
# 1. Identify problematic package
# 2. Check if pre-release or custom assembly
# 3. Revert to direct assembly reference if needed
```

**Priority 2: NU1605 Errors**
```bash
# Find downgrade errors
grep "NU1605" build-log.txt

# Resolution steps:
# 1. Identify conflicting versions
# 2. Update to higher compatible version
# 3. Test transitive dependency compatibility
```

**Priority 3: NU1202 Errors**
```bash
# Find compatibility errors
grep "NU1202" build-log.txt

# Resolution steps:
# 1. Check package framework compatibility
# 2. Find framework-specific version
# 3. Update Directory.Packages.props
```

**Priority 4: NU1010 Errors**
```bash
# Find missing package definitions
grep "NU1010" build-log.txt

# Resolution: Add missing PackageVersion entries
```

**Priority 5: MSB4062 Errors**
```bash
# Find duplicate assembly attribute errors
grep "MSB4062" build-log.txt

# Resolution: Add to affected projects
# <GenerateAssemblyInfo>false</GenerateAssemblyInfo>
```

**Priority 6: NU1506 Warnings**
```bash
# Find duplicate package versions
grep "NU1506" build-log.txt

# Resolution: Remove duplicate entries from Directory.Packages.props
```

#### Step 3.3: Validation After Each Priority
```bash
dotnet restore
dotnet build
# Check error count reduction
```

### Phase 4: Testing and Validation (1-2 hours)

#### Step 4.1: Local Build Validation
```bash
# Clean and rebuild
dotnet clean
dotnet restore
dotnet build --configuration Release
dotnet test
```

#### Step 4.2: Commit and Push
```bash
git add .
git commit -m "Phase X: [Description of changes]"
git push origin feature/central-package-management
```

#### Step 4.3: TeamCity Build Validation
1. Monitor TeamCity build queue
2. Download and analyze build logs
3. Document any remaining issues

### Phase 5: Finalization (30 minutes)

#### Step 5.1: Final Cleanup
- [ ] Remove unused package references
- [ ] Organize Directory.Packages.props by category
- [ ] Add comments for version constraints
- [ ] Update documentation

#### Step 5.2: Success Validation
- [ ] All projects build successfully
- [ ] No blocking errors (NU1103, NU1605, NU1202, NU1010)
- [ ] TeamCity builds pass
- [ ] Package count matches expected

## Rollback Procedures

### Emergency Rollback
```bash
# Revert to previous commit
git reset --hard HEAD~1

# Or revert specific files
git checkout HEAD~1 -- Directory.Packages.props
git checkout HEAD~1 -- "*.csproj"
```

### Partial Rollback
1. Identify problematic changes from build logs
2. Revert specific package changes
3. Re-test incrementally

## Validation Checkpoints

### After Each Phase
- [ ] Solution builds without errors
- [ ] Package restore completes successfully
- [ ] No new warnings introduced
- [ ] TeamCity build status maintained

### Final Validation
- [ ] All NU1103 errors resolved
- [ ] All NU1605 errors resolved
- [ ] All NU1202 errors resolved
- [ ] All NU1010 errors resolved
- [ ] MSB4062 errors resolved
- [ ] NU1506 warnings minimized
- [ ] Build time comparable to previous
- [ ] Package count optimized

## Troubleshooting Quick Reference

### Build Fails Immediately
1. Check Directory.Packages.props syntax
2. Verify ManagePackageVersionsCentrally property
3. Ensure no Version attributes in PackageReference

### Specific Package Issues
1. Check package exists in configured feeds
2. Verify version compatibility with target framework
3. Consider direct assembly reference for problematic packages

### Performance Issues
1. Clear NuGet cache: `dotnet nuget locals all --clear`
2. Check for circular dependencies
3. Optimize package feed configuration

## Success Metrics Dashboard

Track these metrics throughout migration:
- **Error Count by Type:** NU1103, NU1605, NU1202, NU1010, MSB4062, NU1506
- **Build Success Rate:** Percentage of successful builds
- **Build Duration:** Compare before/after migration
- **Package Consolidation:** Reduction in duplicate versions
