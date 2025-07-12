# Central Package Management Best Practices

## Migration Strategy Framework

### Assessment Phase
**Objective:** Understand current state and identify challenges

**Key Activities:**
- Inventory all packages.config files
- Identify pre-release and custom packages
- Document framework targets across projects
- Assess build system compatibility (TeamCity NuGet version)

**Success Criteria:**
- Complete package inventory documented
- Problematic packages identified
- Migration complexity estimated

### Conversion Phase
**Objective:** Systematic conversion with minimal disruption

**Key Activities:**
- Create Directory.Packages.props structure
- Convert packages.config to PackageReference
- Extract versions to central location
- Maintain build functionality

**Success Criteria:**
- All projects use PackageReference format
- Central version management enabled
- No regression in build success

### Resolution Phase
**Objective:** Address all compatibility and configuration issues

**Key Activities:**
- Systematic error resolution by priority
- Version conflict resolution
- Framework compatibility fixes
- Build system integration

**Success Criteria:**
- All blocking errors resolved
- Build success rate maintained
- Package versions optimized

## Package Management Principles

### Version Selection Strategy
1. **Stability First:** Use stable releases over pre-release
2. **Compatibility Focus:** Ensure framework compatibility
3. **Security Priority:** Address known vulnerabilities
4. **Consistency Goal:** Minimize version variations

### Dependency Management
```xml
<!-- Group related packages with consistent versions -->
<!-- AWS SDK packages -->
<PackageVersion Include="AWSSDK.Core" Version="3.7.300.11" />
<PackageVersion Include="AWSSDK.CloudFormation" Version="3.7.300.11" />
<PackageVersion Include="AWSSDK.EC2" Version="3.7.300.11" />
<PackageVersion Include="AWSSDK.RDS" Version="3.7.300.11" />

<!-- Microsoft Extensions packages -->
<PackageVersion Include="Microsoft.Extensions.Logging" Version="3.1.32" />
<PackageVersion Include="Microsoft.Extensions.DependencyInjection" Version="3.1.32" />
<PackageVersion Include="Microsoft.Extensions.Configuration" Version="3.1.32" />
```

### Directory.Packages.props Organization
```xml
<Project>
  <PropertyGroup>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
  </PropertyGroup>
  
  <ItemGroup Label="Core Framework">
    <PackageVersion Include="Microsoft.NETFramework.ReferenceAssemblies" Version="1.0.3" />
    <PackageVersion Include="System.Configuration.ConfigurationManager" Version="8.0.0" />
  </ItemGroup>
  
  <ItemGroup Label="AWS SDK">
    <PackageVersion Include="AWSSDK.Core" Version="3.7.300.11" />
    <PackageVersion Include="AWSSDK.CloudFormation" Version="3.7.300.11" />
  </ItemGroup>
  
  <ItemGroup Label="Testing">
    <PackageVersion Include="FluentAssertions" Version="5.10.3" />
    <PackageVersion Include="Castle.Core" Version="4.4.0" />
  </ItemGroup>
  
  <ItemGroup Label="Utilities">
    <PackageVersion Include="Newtonsoft.Json" Version="13.0.3" />
    <PackageVersion Include="ZstdSharp.Port" Version="0.8.0" />
  </ItemGroup>
</Project>
```

## Error Resolution Methodology

### Systematic Approach
1. **Categorize Errors:** Group by error code and root cause
2. **Prioritize Impact:** Address blocking errors first
3. **Batch Processing:** Fix similar issues together
4. **Validate Incrementally:** Test after each category

### Decision Tree for Package Issues

```
Package Error Detected
├── NU1103 (Package not found)
│   ├── Pre-release package? → Use direct assembly reference
│   ├── Custom package? → Configure private feed or direct reference
│   └── Typo/version issue? → Correct package name/version
├── NU1605 (Package downgrade)
│   ├── Check transitive dependencies
│   ├── Update to minimum required version
│   └── Test for breaking changes
├── NU1202 (Compatibility issue)
│   ├── Find framework-compatible version
│   ├── Consider alternative package
│   └── Update target framework if necessary
└── NU1010 (Missing version)
    ├── Add PackageVersion entry
    ├── Determine appropriate version
    └── Group with related packages
```

## Build System Integration

### TeamCity Considerations
- **NuGet Version:** Ensure 5.4.0+ for CPM support
- **Cache Management:** Clear package cache between builds
- **Artifact Dependencies:** Update package source configurations
- **Build Templates:** Update shared build configurations

### Local Development
```bash
# Standard validation sequence
dotnet clean
dotnet restore
dotnet build --configuration Release
dotnet test

# Package cache management
dotnet nuget locals all --clear
dotnet restore --force
```

### Continuous Integration
```yaml
# Example build pipeline steps
steps:
  - name: Clear NuGet Cache
    run: dotnet nuget locals all --clear
    
  - name: Restore Packages
    run: dotnet restore --verbosity normal
    
  - name: Build Solution
    run: dotnet build --no-restore --configuration Release
    
  - name: Run Tests
    run: dotnet test --no-build --configuration Release
```

## Team Collaboration Practices

### Communication Strategy
1. **Migration Planning:** Share timeline and approach
2. **Progress Updates:** Regular status communication
3. **Issue Escalation:** Clear escalation path for blockers
4. **Knowledge Sharing:** Document decisions and learnings

### Code Review Guidelines
- **Focus Areas:** Package version choices, compatibility decisions
- **Validation:** Ensure build success before approval
- **Documentation:** Require explanation for non-obvious changes
- **Testing:** Verify local and CI build success

### Change Management
```bash
# Recommended commit strategy
git commit -m "CPM: Fix NU1103 errors - revert ManagedLzma to direct reference"
git commit -m "CPM: Resolve NU1605 conflicts - update AWS SDK versions"
git commit -m "CPM: Add missing PackageVersion entries for test packages"
```

## Quality Assurance

### Validation Checklist
- [ ] All projects build successfully
- [ ] No blocking errors (NU1103, NU1605, NU1202, NU1010)
- [ ] Package versions are appropriate and secure
- [ ] Build time performance maintained
- [ ] Test execution successful
- [ ] TeamCity builds pass consistently

### Monitoring and Maintenance
1. **Package Updates:** Regular security and feature updates
2. **Dependency Auditing:** Monitor for vulnerabilities
3. **Performance Tracking:** Build time and package restore metrics
4. **Documentation Updates:** Keep migration guide current

### Success Metrics
- **Error Reduction:** Track specific error code elimination
- **Build Reliability:** Measure build success percentage
- **Maintenance Efficiency:** Time saved in package management
- **Security Posture:** Reduction in vulnerable packages

## Troubleshooting Patterns

### Common Failure Modes
1. **Incomplete Conversion:** Some projects still use packages.config
2. **Version Conflicts:** Transitive dependencies create conflicts
3. **Framework Mismatches:** Packages incompatible with target framework
4. **Build System Issues:** CI/CD pipeline configuration problems

### Recovery Strategies
1. **Incremental Rollback:** Revert specific changes while preserving progress
2. **Selective Fixes:** Address individual packages without full rollback
3. **Alternative Approaches:** Direct references for problematic packages
4. **Escalation Paths:** When to seek additional expertise

### Prevention Measures
1. **Thorough Planning:** Comprehensive pre-migration analysis
2. **Incremental Approach:** Small, testable changes
3. **Automated Validation:** Consistent testing procedures
4. **Documentation:** Record decisions and rationale
