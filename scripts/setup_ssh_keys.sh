#!/bin/bash

# Script to set up SSH keys for GitHub Actions deployment
set -e

VPS_HOST="38.242.229.78"
VPS_USER="julie"
KEY_NAME="autopicker_deploy_key"

echo "🔑 Setting up SSH keys for deployment..."

# Function to generate SSH key pair
generate_ssh_keys() {
    echo "🔐 Generating SSH key pair..."
    
    # Create .ssh directory if it doesn't exist
    mkdir -p ~/.ssh
    
    # Generate SSH key pair
    ssh-keygen -t ed25519 -f ~/.ssh/$KEY_NAME -C "autopicker-deployment" -N ""
    
    echo "✅ SSH key pair generated:"
    echo "   Private key: ~/.ssh/$KEY_NAME"
    echo "   Public key: ~/.ssh/$KEY_NAME.pub"
}

# Function to copy public key to VPS
setup_vps_access() {
    echo "📋 Setting up VPS access..."
    
    # Copy public key to VPS
    ssh-copy-id -i ~/.ssh/$KEY_NAME.pub "$VPS_USER@$VPS_HOST"
    
    # Test the connection
    if ssh -i ~/.ssh/$KEY_NAME -o ConnectTimeout=10 "$VPS_USER@$VPS_HOST" "echo 'SSH key authentication successful'" 2>/dev/null; then
        echo "✅ SSH key authentication working"
    else
        echo "❌ SSH key authentication failed"
        exit 1
    fi
}

# Function to display GitHub secrets setup instructions
display_github_secrets() {
    echo ""
    echo "🔧 GitHub Secrets Setup Instructions:"
    echo "====================================="
    echo ""
    echo "Please add the following secrets to your GitHub repository:"
    echo "(Go to: Settings > Secrets and variables > Actions > New repository secret)"
    echo ""
    echo "1. VPS_SSH_KEY (the private key content):"
    echo "   Name: VPS_SSH_KEY"
    echo "   Value: (copy the content below)"
    echo "   ---"
    cat ~/.ssh/$KEY_NAME
    echo "   ---"
    echo ""
    echo "2. VPS_HOST:"
    echo "   Name: VPS_HOST"
    echo "   Value: $VPS_HOST"
    echo ""
    echo "3. VPS_USER:"
    echo "   Name: VPS_USER"
    echo "   Value: $VPS_USER"
    echo ""
    echo "4. VPS_PATH:"
    echo "   Name: VPS_PATH"
    echo "   Value: /home/julie/autopicker"
    echo ""
    echo "⚠️  IMPORTANT: Keep the private key secure and never share it publicly!"
}

# Function to setup git repository on VPS
setup_vps_repository() {
    echo "📦 Setting up git repository on VPS..."
    ssh -i ~/.ssh/$KEY_NAME "$VPS_USER@$VPS_HOST" << 'ENDSSH'
        # Navigate to home directory
        cd ~
        
        # Clone the repository if it doesn't exist
        if [ ! -d "autopicker" ]; then
            echo "Cloning repository..."
            git clone https://github.com/campersurfer/Autopicker.git autopicker
        else
            echo "Repository already exists, updating..."
            cd autopicker
            git pull origin main
        fi
        
        echo "✅ Repository setup complete"
ENDSSH
}

# Main function
main() {
    echo "🎯 SSH Keys Setup for Autopicker Deployment"
    echo "==========================================="
    
    # Check if key already exists
    if [ -f ~/.ssh/$KEY_NAME ]; then
        echo "⚠️  SSH key already exists at ~/.ssh/$KEY_NAME"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Skipping key generation..."
        else
            generate_ssh_keys
        fi
    else
        generate_ssh_keys
    fi
    
    setup_vps_access
    setup_vps_repository
    display_github_secrets
    
    echo ""
    echo "🎉 SSH keys setup completed!"
    echo "📝 Next steps:"
    echo "   1. Add the GitHub secrets shown above"
    echo "   2. Push your code to trigger the deployment"
    echo "   3. Monitor the GitHub Actions workflow"
}

# Run main function
main "$@"