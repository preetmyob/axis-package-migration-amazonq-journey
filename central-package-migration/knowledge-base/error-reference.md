# Central Package Management Error Reference Guide

## Error Code Quick Reference

| Error Code | Severity | Description | Common Cause | Quick Fix |
|------------|----------|-------------|--------------|-----------|
| NU1103 | Error | Unable to find package | Pre-release/custom packages | Use direct assembly reference |
| NU1605 | Error | Detected package downgrade | Version conflicts | Update to higher version |
| NU1202 | Error | Package not compatible | Framework mismatch | Use compatible version |
| NU1010 | Error | Package reference without version | Missing PackageVersion | Add to Directory.Packages.props |
| NU1008 | Warning | Package vulnerability | Security issue | Update to patched version |
| NU1506 | Warning | Duplicate package version | Multiple entries | Remove duplicates |
| MSB4062 | Error | Duplicate assembly attributes | Auto-generation conflict | Set GenerateAssemblyInfo=false |

## Detailed Error Solutions

### NU1103: Unable to find package 'X' with version 'Y'

**Root Causes:**
1. Pre-release packages not available in standard feeds
2. Custom/internal packages not in configured sources
3. Package name or version typos
4. Private feed authentication issues

**Solution Strategies:**

**Strategy 1: Direct Assembly Reference (Recommended for problematic packages)**
```xml
<!-- Remove PackageReference -->
<!-- <PackageReference Include="ManagedLzma" /> -->

<!-- Add direct reference -->
<Reference Include="ManagedLzma">
  <HintPath>..\..\packages\ManagedLzma.0.2.0-alpha-6\lib\net20\ManagedLzma.dll</HintPath>
</Reference>
```

**Strategy 2: Configure Package Sources**
```xml
<!-- In NuGet.Config -->
<packageSources>
  <add key="nuget.org" value="https://api.nuget.org/v3/index.json" />
  <add key="internal-feed" value="https://internal.company.com/nuget" />
</packageSources>
```

**Strategy 3: Version Correction**
```xml
<!-- Check actual available versions -->
<PackageVersion Include="PackageName" Version="1.0.0" />
```

**Real Example from Migration:**
```xml
<!-- Problem: ManagedLzma 0.2.0-alpha-6 not found -->
<!-- Solution: Reverted to direct reference -->
<Reference Include="ManagedLzma">
  <HintPath>..\..\packages\ManagedLzma.0.2.0-alpha-6\lib\net20\ManagedLzma.dll</HintPath>
</Reference>
```

### NU1605: Detected package downgrade

**Root Causes:**
1. Transitive dependencies require higher versions
2. Explicit version constraints too restrictive
3. Framework-specific version requirements

**Solution Process:**
1. Identify the conflicting packages from error message
2. Find the minimum required version
3. Update Directory.Packages.props with compatible version
4. Test for breaking changes

**Real Examples from Migration:**
```xml
<!-- Problem: AWSSDK.Core downgrade from 3.7.300.11 to 3.7.103.50 -->
<!-- Solution: Update to required version -->
<PackageVersion Include="AWSSDK.Core" Version="3.7.300.11" />

<!-- Problem: ZstdSharp.Port downgrade -->
<!-- Solution: Update to compatible version -->
<PackageVersion Include="ZstdSharp.Port" Version="0.8.0" />

<!-- Problem: System.Configuration.ConfigurationManager downgrade -->
<!-- Solution: Update to latest compatible -->
<PackageVersion Include="System.Configuration.ConfigurationManager" Version="8.0.0" />
```

### NU1202: Package 'X' with version 'Y' is not compatible with framework 'Z'

**Root Causes:**
1. Package doesn't support target framework (.NET Framework 4.8)
2. Using .NET Core/5+ specific package versions
3. Framework-specific dependencies missing

**Solution Strategies:**

**Strategy 1: Find Framework-Compatible Version**
```xml
<!-- Problem: FluentAssertions 6.x not compatible with .NET Framework 4.8 -->
<!-- Solution: Use 5.x version -->
<PackageVersion Include="FluentAssertions" Version="5.10.3" />
```

**Strategy 2: Multi-Target Package Selection**
```xml
<!-- Choose version that supports multiple frameworks -->
<PackageVersion Include="Microsoft.Extensions.Logging" Version="3.1.32" />
```

**Real Examples from Migration:**
```xml
<!-- FluentAssertions compatibility fix -->
<PackageVersion Include="FluentAssertions" Version="5.10.3" />

<!-- ZstdSharp.Port compatibility -->
<PackageVersion Include="ZstdSharp.Port" Version="0.8.0" />

<!-- Common.Logging compatibility -->
<PackageVersion Include="Common.Logging" Version="3.4.1" />
```

### NU1010: Package reference 'X' does not contain a version

**Root Causes:**
1. PackageReference exists in project but no PackageVersion in Directory.Packages.props
2. Incomplete migration from packages.config
3. Missing entries after bulk conversion

**Solution Process:**
1. Identify all missing PackageVersion entries
2. Determine appropriate versions (check packages.config history)
3. Add to Directory.Packages.props
4. Group related packages together

**Batch Solution Script:**
```python
# Extract missing packages from build log
missing_packages = [
    "Castle.Core", "Fare", "System.Diagnostics.DiagnosticSource",
    "Microsoft.Extensions.Logging", "Microsoft.Extensions.DependencyInjection",
    # ... more packages
]

# Generate PackageVersion entries
for package in missing_packages:
    print(f'<PackageVersion Include="{package}" Version="[VERSION]" />')
```

**Real Examples from Migration:**
```xml
<!-- Missing AWS SDK packages -->
<PackageVersion Include="AWSSDK.CloudFormation" Version="3.7.300.11" />
<PackageVersion Include="AWSSDK.EC2" Version="3.7.300.11" />
<PackageVersion Include="AWSSDK.RDS" Version="3.7.300.11" />

<!-- Missing testing packages -->
<PackageVersion Include="Castle.Core" Version="4.4.0" />
<PackageVersion Include="Fare" Version="2.1.1" />

<!-- Missing system packages -->
<PackageVersion Include="System.Diagnostics.DiagnosticSource" Version="4.7.1" />
```

### MSB4062: Duplicate assembly attribute errors

**Root Causes:**
1. Auto-generated assembly attributes conflict with SharedAssemblyInfo.cs
2. Multiple projects defining same attributes
3. .NET SDK auto-generation enabled

**Solution:**
```xml
<!-- Add to each affected project -->
<PropertyGroup>
  <GenerateAssemblyInfo>false</GenerateAssemblyInfo>
</PropertyGroup>
```

**Batch Fix Script:**
```python
import os
import re

def fix_assembly_info(project_path):
    with open(project_path, 'r') as f:
        content = f.read()
    
    # Add GenerateAssemblyInfo property
    if '<GenerateAssemblyInfo>false</GenerateAssemblyInfo>' not in content:
        # Insert after first PropertyGroup
        content = re.sub(
            r'(<PropertyGroup>)',
            r'\1\n    <GenerateAssemblyInfo>false</GenerateAssemblyInfo>',
            content, count=1
        )
        
        with open(project_path, 'w') as f:
            f.write(content)
```

### NU1506: Duplicate package version

**Root Causes:**
1. Multiple PackageVersion entries for same package
2. Copy-paste errors in Directory.Packages.props
3. Merge conflicts

**Detection:**
```bash
# Find duplicates in Directory.Packages.props
sort Directory.Packages.props | uniq -d
```

**Solution:**
```xml
<!-- Remove duplicate entries, keep one -->
<!-- WRONG: -->
<PackageVersion Include="System.Diagnostics.DiagnosticSource" Version="4.7.1" />
<PackageVersion Include="System.Diagnostics.DiagnosticSource" Version="4.7.1" />

<!-- CORRECT: -->
<PackageVersion Include="System.Diagnostics.DiagnosticSource" Version="4.7.1" />
```

## Problem Categories and Patterns

### Architectural Issues
- **Symptoms:** NU1103 errors for specific packages
- **Pattern:** Pre-release or custom assemblies
- **Strategy:** Direct assembly references

### Version Conflicts
- **Symptoms:** NU1605 downgrade errors
- **Pattern:** Transitive dependency requirements
- **Strategy:** Version harmonization

### Framework Compatibility
- **Symptoms:** NU1202 compatibility errors
- **Pattern:** Modern packages on legacy frameworks
- **Strategy:** Framework-specific versions

### Migration Gaps
- **Symptoms:** NU1010 missing version errors
- **Pattern:** Incomplete conversion process
- **Strategy:** Systematic gap filling

### Build System Issues
- **Symptoms:** MSB4062 duplicate attributes
- **Pattern:** Auto-generation conflicts
- **Strategy:** Disable auto-generation

## Best Practices by Error Type

### Prevention Strategies
1. **Pre-Migration Analysis:** Identify problematic packages early
2. **Incremental Approach:** Fix one error category at a time
3. **Version Strategy:** Use exact versions for stability
4. **Testing Cadence:** Validate after each major change

### Resolution Priorities
1. **Blocking Errors First:** NU1103, NU1605, NU1202, NU1010
2. **Build Issues Second:** MSB4062
3. **Warnings Last:** NU1506, NU1008

### Validation Techniques
1. **Local Testing:** `dotnet restore && dotnet build`
2. **Clean Builds:** `dotnet clean` before validation
3. **Log Analysis:** Systematic error pattern matching
4. **Incremental Commits:** Track progress and enable rollback
