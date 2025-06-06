#!/usr/bin/env sh
export JAVA_HOME=${JAVA_HOME:-$(/usr/libexec/java_home)}
exec ./gradle/wrapper/gradle-wrapper.jar "$@"
