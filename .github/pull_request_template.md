# Pull Request

## Description
<!-- Provide a brief description of the changes in this PR -->

## Type of Change
<!-- Mark the relevant option with an "x" -->
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Configuration/setup change
- [ ] 🧪 Test improvement
- [ ] ♻️ Code refactoring (no functional changes)

## Component(s) Affected
<!-- Mark all that apply -->
- [ ] 🔐 Authentication Server
- [ ] 🐳 Docker Configuration  
- [ ] 📋 Task Documentation
- [ ] 🔧 CI/CD Pipeline
- [ ] 📖 Documentation
- [ ] 🧪 Tests

## Changes Made
<!-- List the main changes made in this PR -->
- 
- 
- 

## Testing
<!-- Describe the tests you ran to verify your changes -->
- [ ] All existing tests pass (`uv run pytest`)
- [ ] Added new tests for new functionality
- [ ] Manual testing performed
- [ ] Integration tests pass
- [ ] Docker build succeeds

### Test Commands Run
```bash
# Add the commands you used to test your changes
uv run pytest tests/ -v
uv run ruff check .
# etc.
```

## Security Considerations
<!-- If this PR affects security, describe the considerations -->
- [ ] This PR does not introduce security vulnerabilities
- [ ] No sensitive data is exposed
- [ ] Input validation is properly implemented
- [ ] Authentication/authorization is properly handled

## Breaking Changes
<!-- If this is a breaking change, describe what breaks and how to migrate -->
- None

## Documentation
<!-- How is this change documented? -->
- [ ] Code comments updated
- [ ] README updated
- [ ] API documentation updated
- [ ] No documentation needed

## Deployment Notes
<!-- Any special considerations for deployment -->
- [ ] Requires database migration
- [ ] Requires environment variable updates
- [ ] Requires Docker image rebuild
- [ ] No special deployment steps needed

## Related Issues
<!-- Link to related issues -->
Fixes #
Closes #
Related to #

## Screenshots/Logs
<!-- If applicable, add screenshots or relevant logs -->

## Checklist
<!-- Mark completed items with an "x" -->
- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Review Notes
<!-- Any specific areas you'd like reviewers to focus on -->
Please pay special attention to:
- 
- 

---
<!-- 
For maintainers:
- Ensure all CI checks pass
- Verify code follows established patterns
- Check for potential security issues
- Validate test coverage
-->

/cc @team-leads