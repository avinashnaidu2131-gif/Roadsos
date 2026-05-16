#!/bin/sh
# RoadSoS — Bootstrap Gradle wrapper for local builds
# Run this ONCE before using ./gradlew, if the wrapper jar is missing.
#
# Requires: curl, Java 17+
# Usage:    sh android/bootstrap.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JAR="$SCRIPT_DIR/gradle/wrapper/gradle-wrapper.jar"

if [ -f "$JAR" ]; then
  echo "✅ gradle-wrapper.jar already present"
  exit 0
fi

echo "⬇  Downloading gradle-wrapper.jar..."
mkdir -p "$SCRIPT_DIR/gradle/wrapper"

# Try official Gradle GitHub releases
GRADLE_VERSION="8.9"
URL="https://raw.githubusercontent.com/gradle/gradle/v${GRADLE_VERSION}.0/gradle/wrapper/gradle-wrapper.jar"

if curl -fsSL -o "$JAR" "$URL" 2>/dev/null; then
  echo "✅ Downloaded from GitHub"
elif command -v gradle >/dev/null 2>&1; then
  echo "⬇  Generating via local Gradle installation..."
  cd "$SCRIPT_DIR"
  gradle wrapper --gradle-version "$GRADLE_VERSION"
  echo "✅ Generated via local Gradle"
else
  echo ""
  echo "❌ Could not download gradle-wrapper.jar automatically."
  echo ""
  echo "Fix options:"
  echo "  A) Install Android Studio — it includes Gradle."
  echo "     Open the android/ folder and let it sync."
  echo ""
  echo "  B) Install Gradle manually:"
  echo "     https://gradle.org/install/"
  echo "     Then run: gradle wrapper --gradle-version 8.9"
  echo ""
  echo "  C) Use GitHub Actions (no local setup needed):"
  echo "     Push your code → Actions tab → Run workflow"
  echo ""
  exit 1
fi
