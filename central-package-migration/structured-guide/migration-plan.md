# Central Package Management Migration Guide

## Executive Summary

This guide documents the complete process for migrating .NET solutions from packages.config to Central Package Management (CPM), based on the successful migration of the Axis platform containing 50+ projects.

**Key Outcomes Achieved:**
- 95%+ migration completion with all blocking errors resolved
- Systematic resolution of 6 major error categories (NU1103, NU1605, NU1202, NU1010, NU1008, NU1506)
- Created reusable automation scripts for future migrations
- Established best practices for enterprise build environments

## Migration Methodology

### Phase 1: Pre-Migration Assessment
1. **Inventory Current State**
   - Count total projects and package references
   - Identify pre-release and problematic packages
   - Document custom assembly references

2. **Environment Preparation**
   - Ensure NuGet client version compatibility (5.4.0+ for TeamCity)
   - Create feature branch for migration work
   - Set up local testing environment

### Phase 2: Initial Conversion
1. **Enable Central Package Management**
   ```xml
   <!-- Create Directory.Packages.props in solution root -->
   <Project>
     <PropertyGroup>
       <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
     </PropertyGroup>
     <ItemGroup>
       <!-- Package versions will be defined here -->
     </ItemGroup>
   </Project>
   ```

2. **Convert Project Files**
   - Remove Version attributes from PackageReference elements
   - Migrate packages.config to PackageReference format
   - Consolidate package versions in Directory.Packages.props

### Phase 3: Error Resolution (Priority Order)

#### 1. Architectural Issues (NU1103)
**Problem:** Pre-release packages causing resolution failures
**Solution:** Revert to direct assembly references
```xml
<!-- Replace PackageReference with direct reference -->
<Reference Include="ManagedLzma">
  <HintPath>path\to\assembly.dll</HintPath>
</Reference>
```

#### 2. Version Conflicts (NU1605)
**Problem:** Package downgrades due to transitive dependencies
**Solution:** Update to compatible versions
```xml
<PackageVersion Include="AWSSDK.Core" Version="3.7.300.11" />
<PackageVersion Include="ZstdSharp.Port" Version="0.8.0" />
```

#### 3. Compatibility Issues (NU1202)
**Problem:** Packages incompatible with target framework
**Solution:** Use framework-compatible versions
```xml
<PackageVersion Include="FluentAssertions" Version="5.10.3" />
```

#### 4. Missing Definitions (NU1010)
**Problem:** PackageReference without corresponding PackageVersion
**Solution:** Add missing entries to Directory.Packages.props

#### 5. Build Attribute Conflicts (MSB4062)
**Problem:** Duplicate assembly attributes
**Solution:** Disable auto-generation
```xml
<PropertyGroup>
  <GenerateAssemblyInfo>false</GenerateAssemblyInfo>
</PropertyGroup>
```

#### 6. Duplicate Entries (NU1506)
**Problem:** Multiple PackageVersion entries for same package
**Solution:** Remove duplicates, keep single entry

### Phase 4: Validation and Testing
1. **Local Validation**
   ```bash
   dotnet restore
   dotnet build
   ```

2. **Build System Testing**
   - Commit changes to feature branch
   - Monitor TeamCity build results
   - Analyze build logs for remaining issues

3. **Iterative Refinement**
   - Address any remaining warnings
   - Optimize package versions
   - Document any workarounds

## Common Error Patterns and Solutions

### NU1103: Unable to find package
- **Cause:** Pre-release packages, private feeds, or assembly references
- **Solution:** Use direct assembly references or update package sources

### NU1605: Detected package downgrade
- **Cause:** Transitive dependencies requiring higher versions
- **Solution:** Update package to compatible version

### NU1202: Package is not compatible
- **Cause:** Package doesn't support target framework
- **Solution:** Find framework-compatible version or alternative

### NU1010: Package reference without version
- **Cause:** Missing PackageVersion in Directory.Packages.props
- **Solution:** Add PackageVersion entry

### MSB4062: Duplicate assembly attributes
- **Cause:** Auto-generated attributes conflict with SharedAssemblyInfo.cs
- **Solution:** Set GenerateAssemblyInfo to false

### NU1506: Duplicate package version
- **Cause:** Multiple PackageVersion entries for same package
- **Solution:** Remove duplicates

## Best Practices

### Package Management
- Use exact versions for stability
- Group related packages (e.g., AWS SDK components)
- Document any version constraints or compatibility requirements

### Project Structure
- Keep Directory.Packages.props organized by category
- Use comments to explain version choices
- Maintain consistent formatting

### Build Integration
- Test locally before committing
- Use incremental commits for easier troubleshooting
- Monitor build logs systematically

### Team Collaboration
- Document migration decisions
- Share reusable scripts and tools
- Establish review process for package updates

## Success Metrics

- **Error Reduction:** Track specific error codes (NU1103, NU1605, etc.)
- **Build Success Rate:** Monitor TeamCity build success percentage
- **Package Consolidation:** Measure reduction in duplicate package versions
- **Maintenance Efficiency:** Time saved in package management tasks

## Next Steps

1. **Complete Migration:** Address any remaining non-blocking warnings
2. **Documentation:** Update team documentation and onboarding materials
3. **Automation:** Implement automated package update processes
4. **Monitoring:** Set up alerts for package security vulnerabilities
5. **Training:** Share knowledge with other teams attempting similar migrations
