## Cmake notes 

### link to user shared library via pkgconfig 

Sometimes cmake will use pkg_search_module to find shared library. 
User without root access cannot make change to `pkg-config`. A quick fix would be the follwing solution.

`set(ENV{PKG_CONFIG_PATH} "$ENV{PKG_CONFIG_PATH}:/path/to/user/lib/pkgconfig")`

`pkg_search_module(protobuf REQUIRED IMPORTED_TARGET GLOBAL protobuf>=3.0.0)`

pkg_search_module cannot find protobuf in the system's pkg-config because it is not installed via system package 
manager. The line added before search tells cmake to look up a customized directory to use the pkgconfig file. 
This is used in MGARD. 

### Always full RPATH

```
 message(STATUS "Rpath")
  set(CMAKE_SKIP_BUILD_RPATH FALSE)
  set(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE)
  set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_LIBDIR}")
  set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
  list(FIND CMAKE_PLATFORM_IMPLICIT_LINK_DIRECTORIES "${CMAKE_INSTALL_LIBDIR}" isSystemDir)
  if("${isSystemDir}" STREQUAL "-1")
      set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_LIBDIR}")
  endif("${isSystemDir}" STREQUAL "-1")
```
