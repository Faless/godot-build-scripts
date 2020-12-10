#!/bin/bash

set -e

# Config

export BUILD_NAME=official
export SCONS="scons -j${NUM_CORES} verbose=yes warnings=no progress=no"
export OPTIONS="debug_symbols=no use_lto=yes"
export OPTIONS_MONO="use_lto=no module_mono_enabled=yes mono_static=yes mono_prefix=/root/mono-installs/wasm-runtime-release"
export TERM=xterm

rm -rf godot
mkdir godot
cd godot
tar xf /root/godot.tar.gz --strip-components=1

# Classical

if [ "${CLASSICAL}" == "1" ]; then
  echo "Starting classical build for JavaScript..."

  source /root/emsdk_2.0.10/emsdk_env.sh

  $SCONS platform=javascript ${OPTIONS} target=release_debug gdnative_enabled=yes tools=no
  $SCONS platform=javascript ${OPTIONS} target=release_debug threads_enabled=yes tools=no
  $SCONS platform=javascript ${OPTIONS} target=release_debug tools=no

  $SCONS platform=javascript ${OPTIONS} target=release gdnative_enabled=yes tools=no
  $SCONS platform=javascript ${OPTIONS} target=release threads_enabled=yes tools=no
  $SCONS platform=javascript ${OPTIONS} target=release tools=no

  mkdir -p /root/out/templates
  cp -rvp bin/*.zip /root/out/templates
  rm -f bin/*.zip
fi

# Mono

if [ "${MONO}" == "1" ]; then
  echo "Starting Mono build for JavaScript..."

  source /root/emsdk_1.39.9/emsdk_env.sh

  cp /root/mono-glue/*.cpp modules/mono/glue/
  cp -r /root/mono-glue/GodotSharp/GodotSharp/Generated modules/mono/glue/GodotSharp/GodotSharp/
  cp -r /root/mono-glue/GodotSharp/GodotSharpEditor/Generated modules/mono/glue/GodotSharp/GodotSharpEditor/

  $SCONS platform=javascript ${OPTIONS} ${OPTIONS_MONO} target=release_debug tools=no
  $SCONS platform=javascript ${OPTIONS} ${OPTIONS_MONO} target=release tools=no

  mkdir -p /root/out/templates-mono
  cp -rvp bin/*.zip /root/out/templates-mono
  rm -f bin/*.zip

  mkdir -p /root/out/templates-mono/bcl
  cp -r /root/mono-installs/wasm-bcl/wasm /root/out/templates-mono/bcl/
fi

echo "JavaScript build successful"
