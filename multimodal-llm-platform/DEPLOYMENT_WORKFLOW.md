# Julie's Standard Deployment Workflow

## Development Process
- **Local Development**: Work on code locally on Mac
- **Version Control**: Commit directly to main branch (single developer workflow)
- **Testing**: Julie tests with real-world use cases (constitutional analysis documents)
- **Repository**: GitHub with CLI access configured

## Production Environment
- **VPS Provider**: Contabo
- **Server Access**: `ssh julie@38.242.229.78`  
- **Auto-Deploy**: VPS pulls from GitHub automatically
- **Runtime**: 24/7 operation with auto-updates on every commit
- **Multi-Project**: Multiple projects running on same VPS

## Scaling Options
- **Current**: Existing Contabo VPS (can upgrade easily)
- **Alternative Providers**: Evaluate if more capacity needed at better cost

## Deployment Strategy
1. Develop and test locally
2. Commit to main branch
3. VPS automatically pulls and updates
4. Production service restarts with new code

## Key Principles
- **Simplicity**: Direct main branch deployment
- **Automation**: Zero-manual deployment steps
- **Real-world Testing**: Use actual use cases for validation
- **Cost-Effective**: Leverage existing VPS infrastructure

This workflow prioritizes speed of iteration and real-world testing over complex CI/CD pipelines, perfect for a single-developer product with known use cases.