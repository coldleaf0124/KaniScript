#!/usr/bin/env bash
set -e

REPO_URL="https://github.com/coldleaf0124/kaniscript.git"
INSTALL_DIR="$HOME/.kaniscript"

# Determine source directory
if [ -n "${BASH_SOURCE[0]}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    # Piped into bash: clone or update in ~/.kaniscript
    echo "Cloning KaniScript to $INSTALL_DIR..."
    if [ -d "$INSTALL_DIR" ]; then
        git -C "$INSTALL_DIR" pull --ff-only || true
    else
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi
    DIR="$INSTALL_DIR"
fi

BIN_DIR="$DIR/bin"

echo "=================================================="
echo " 🦀 KaniScript (kani / ks) Installer"
echo "=================================================="

# Ensure bin scripts are executable
chmod +x "$BIN_DIR/kani" "$BIN_DIR/ks"

# Try installing symlinks to ~/.local/bin if available and in PATH
INSTALLED_SYMLINK=false
TARGET_BIN="$HOME/.local/bin"
if [ -d "$TARGET_BIN" ] && [[ ":$PATH:" == *":$TARGET_BIN:"* ]]; then
    if ln -sf "$BIN_DIR/kani" "$TARGET_BIN/kani" 2>/dev/null && ln -sf "$BIN_DIR/ks" "$TARGET_BIN/ks" 2>/dev/null; then
        echo "✓ Created symlinks in $TARGET_BIN (already in your PATH)"
        INSTALLED_SYMLINK=true
    fi
fi

if [ "$INSTALLED_SYMLINK" = false ]; then
    # Detect user shell config file
    SHELL_NAME="$(basename "$SHELL")"
    if [ "$SHELL_NAME" = "zsh" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ "$SHELL_NAME" = "bash" ]; then
        SHELL_RC="$HOME/.bashrc"
        [ -f "$HOME/.bash_profile" ] && SHELL_RC="$HOME/.bash_profile"
    else
        SHELL_RC="$HOME/.profile"
    fi

    EXPORT_LINE="export PATH=\"$BIN_DIR:\$PATH\""

    if grep -Fxq "$EXPORT_LINE" "$SHELL_RC" 2>/dev/null; then
        echo "✓ PATH already configured in $SHELL_RC"
    else
        if (echo "" >> "$SHELL_RC" && echo "# KaniScript CLI" >> "$SHELL_RC" && echo "$EXPORT_LINE" >> "$SHELL_RC") 2>/dev/null; then
            echo "✓ Added KaniScript to PATH in $SHELL_RC"
        else
            echo "ℹ Could not auto-modify $SHELL_RC. Please add this manually:"
            echo "  $EXPORT_LINE"
        fi
    fi

    echo ""
    echo "To activate immediately, run:"
    echo "  source $SHELL_RC"
    echo "Or run manually:"
    echo "  $EXPORT_LINE"
fi

echo ""
echo "Verify installation:"
echo "  kani run examples/01_hello.ks"
echo "  ks run examples/02_fibonacci.ks"
echo "=================================================="
