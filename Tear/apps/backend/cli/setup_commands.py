"""
Setup Commands
==============

CLI commands for configuring API providers.
"""

from pathlib import Path
from core.provider_config import get_provider, PROVIDERS
from ui import print_status, bold, box, Icons, icon, highlight, success, warning
from .utils import print_banner


import os
from pathlib import Path
from core.provider_config import get_provider, PROVIDERS
from ui import print_status, bold, box, Icons, icon, highlight, success, warning, muted
from .utils import print_banner


def set_env_var(key: str, value: str, project_dir: Path) -> bool:
    """
    Update or add an environment variable in the .env file.
    
    Args:
        key: Variable name
        value: Variable value
        project_dir: Project root directory
    
    Returns:
        True if successful
    """
    env_path = project_dir / ".env"
    
    # Create .env if it doesn't exist
    if not env_path.exists():
        env_path.touch()
        
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
        updated = False
        new_lines = []
        
        # Format the line
        # If value has spaces or special chars, quote it
        safe_value = value
        if any(c in value for c in (" ", "\"", "'", "$", "\\")):
            safe_value = f'"{value.replace("\\", "\\\\").replace("\"", "\\\"")}"'
            
        new_line = f"{key}={safe_value}"
        
        for line in lines:
            if line.startswith(f"{key}="):
                new_lines.append(new_line)
                updated = True
            else:
                new_lines.append(line)
                
        if not updated:
            new_lines.append(new_line)
            
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        return True
    except Exception as e:
        print_status(f"Failed to update .env: {e}", "error")
        return False


def handle_setup_command(provider_id: str, project_dir: Path) -> None:
    """
    Handle the --setup command for a specific provider.
    
    Args:
        provider_id: The ID of the provider (CLAUDE, OPENROUTER, GEMINI)
        project_dir: The project root directory
    """
    provider = get_provider(provider_id)
    if not provider:
        print_status(f"Unknown provider: {provider_id}", "error")
        print(f"Available providers: {', '.join(PROVIDERS.keys())}")
        return

    print_banner()
    print(f"\n{icon(Icons.SETUP)}  Configuring: {bold(provider.name)}")
    print(muted("-" * 40))

    if provider_id.upper() == "CLAUDE":
        print("\nAnthropic Claude uses OAuth authentication via Claude Code CLI.")
        print(f"To setup, run: {highlight('claude /login')} in your terminal.")
        print("\nIf you have a manual token, you can set it below.")
        
    # Prompt for API Key
    prompt_msg = f"Enter your {provider.auth_env_var}: "
    if provider_id.upper() == "CLAUDE":
        prompt_msg = "Enter your CLAUDE_CODE_OAUTH_TOKEN (optional, press Enter to skip): "
        
    try:
        api_key = input(prompt_msg).strip()
        
        if api_key:
            if set_env_var(provider.auth_env_var, api_key, project_dir):
                print_status(f"Saved {provider.auth_env_var} to .env", "success")
        elif provider_id.upper() != "CLAUDE":
            print_status("No key provided. Setup cancelled.", "warning")
            return

        # Save provider selection
        if set_env_var("AUTO_BUILD_PROVIDER", provider_id.upper(), project_dir):
            print_status(f"Set active provider to {provider_id.upper()}", "success")

        # Prompt for default model
        print(f"\nDefault model for {provider.name} is: {highlight(provider.default_model)}")
        custom_model = input(f"Enter custom model ID (or press Enter to keep default): ").strip()
        
        active_model = custom_model if custom_model else provider.default_model
        if set_env_var("ANTHROPIC_MODEL", active_model, project_dir):
            print_status(f"Default model set to {active_model}", "success")

        # Set base URL if provider has one
        if provider.base_url:
            if set_env_var("ANTHROPIC_BASE_URL", provider.base_url, project_dir):
                print_status(f"Set API endpoint to {provider.base_url}", "success")
        elif provider_id.upper() == "CLAUDE":
            # Clear base URL for native Claude to use default
            set_env_var("ANTHROPIC_BASE_URL", "", project_dir)

        print("\n" + success(f"✅ {provider.name} setup complete!"))
        print(muted("The engine will now use this provider by default."))
        print(f"Model will default to: {highlight(provider.default_model)}")

    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
    except Exception as e:
        print_status(f"An unexpected error occurred: {e}", "error")
