import os
from conan import ConanFile
from conan.tools.meson import MesonToolchain, Meson
from conan.tools.layout import basic_layout
from conan.tools.files import copy, get

class PangoConan(ConanFile):
    name = "pango"
    version = "1.50.10"
    package_type = "library"

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False], "with_libthai": [True, False], "with_cairo": [True, False], "with_xft": [True, False, "auto"], "with_freetype": [True, False, "auto"], "with_fontconfig": [True, False, "auto"]}
    default_options = {"shared": True, "fPIC": True, "with_libthai": False, "with_cairo": True, "with_xft": "auto", "with_freetype": "auto", "with_fontconfig": "auto"}

    tool_requires = "meson/1.2.2"
    generators = "PkgConfigDeps"

    def requirements(self):
        if self.options.with_freetype:
            self.requires("freetype/2.13.0", transitive_headers=True)

        if self.options.with_fontconfig:
            self.requires("fontconfig/2.14.2", transitive_headers=True)
        if self.options.with_xft:
            self.requires("libxft/2.3.8", transitive_headers=True)
        if self.options.with_xft and self.options.with_fontconfig and self.options.with_freetype:
            self.requires("xorg/system", transitive_headers=True)    # for xorg::xrender
        if self.options.with_cairo:
            self.requires("cairo/1.17.6", transitive_headers=True)

        self.requires("harfbuzz/8.2.1", transitive_headers=True)
        self.requires("glib/2.78.0", transitive_headers=True)
        self.requires("fribidi/1.0.13", transitive_headers=True)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def config_options(self):
        if self.options.shared or self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

        if self.options.with_xft == "auto":
            self.options.with_xft = self.settings.os in ["Linux", "FreeBSD"]
        if self.options.with_freetype == "auto":
            self.options.with_freetype = self.settings.os not in ["Windows", "Macos"]
        if self.options.with_fontconfig == "auto":
            self.options.with_fontconfig = self.settings.os not in ["Windows", "Macos"]
        if self.options.shared:
            self.options["glib"].shared = True
            self.options["harfbuzz"].shared = True
            if self.options.with_cairo:
                self.options["cairo"].shared = True

    def layout(self):
        basic_layout(self)

    def generate(self):
        tc = MesonToolchain(self)
        tc.project_options["introspection"] = "disabled"

        tc.project_options["libthai"] = "enabled" if self.options.with_libthai else "disabled"
        tc.project_options["cairo"] = "enabled" if self.options.with_cairo else "disabled"
        tc.project_options["xft"] = "enabled" if self.options.with_xft else "disabled"
        tc.project_options["fontconfig"] = "enabled" if self.options.with_fontconfig else "disabled"
        tc.project_options["freetype"] = "enabled" if self.options.with_freetype else "disabled"

        tc.generate()

    def build(self):
        meson = Meson(self)
        meson.configure()
        meson.build()

    def package(self):
        copy(self, pattern="COPYING", dst="licenses", src=self.source_folder)
        meson = Meson(self)
        meson.install()

    def package_info(self):
        self.cpp_info.components['pango_'].libs = ['pango-1.0']
        self.cpp_info.components['pango_'].names['pkg_config'] = 'pango'

        if self.settings.os in ["Linux","FreeBSD"]:
            self.cpp_info.components['pango_'].system_libs.append("m")

        self.cpp_info.components['pango_'].requires.append('glib::glib-2.0')
        self.cpp_info.components['pango_'].requires.append('glib::gobject-2.0')
        self.cpp_info.components['pango_'].requires.append('glib::gio-2.0')
        self.cpp_info.components['pango_'].requires.append('fribidi::fribidi')
        self.cpp_info.components['pango_'].requires.append('harfbuzz::harfbuzz')

        if self.options.with_fontconfig:
            self.cpp_info.components['pango_'].requires.append('fontconfig::fontconfig')

        if self.options.with_xft:
            self.cpp_info.components['pango_'].requires.append('libxft::libxft')
            # Pango only uses xrender when Xft, fontconfig and freetype are enabled
            if self.options.with_fontconfig and self.options.with_freetype:
                self.cpp_info.components['pango_'].requires.append('xorg::xrender')
        if self.options.with_cairo:
            self.cpp_info.components['pango_'].requires.append('cairo::cairo_')
        self.cpp_info.components['pango_'].includedirs = [os.path.join(self.package_folder, "include", "pango-1.0")]

        if self.options.with_freetype:
            self.cpp_info.components['pangoft2'].libs = ['pangoft2-1.0']
            self.cpp_info.components['pangoft2'].names['pkg_config'] = 'pangoft2'
            self.cpp_info.components['pangoft2'].requires = ['pango_', 'freetype::freetype']
            self.cpp_info.components['pangoft2'].includedirs = [os.path.join(self.package_folder, "include", "pango-1.0")]

        if self.options.with_fontconfig:
            self.cpp_info.components['pangofc'].names['pkg_config'] = 'pangofc'
            if self.options.with_freetype:
                self.cpp_info.components['pangofc'].requires = ['pangoft2']

        if self.settings.os != "Windows":
            self.cpp_info.components['pangoroot'].names['pkg_config'] = 'pangoroot'
            if self.options.with_freetype:
                self.cpp_info.components['pangoroot'].requires = ['pangoft2']

        if self.options.with_xft:
            self.cpp_info.components['pangoxft'].libs = ['pangoxft-1.0']
            self.cpp_info.components['pangoxft'].names['pkg_config'] = 'pangoxft'
            self.cpp_info.components['pangoxft'].requires = ['pango_', 'pangoft2']
            self.cpp_info.components['pangoxft'].includedirs = [os.path.join(self.package_folder, "include", "pango-1.0")]

        if self.settings.os == "Windows":
            self.cpp_info.components['pangowin32'].libs = ['pangowin32-1.0']
            self.cpp_info.components['pangowin32'].names['pkg_config'] = 'pangowin32'
            self.cpp_info.components['pangowin32'].requires = ['pango_']
            self.cpp_info.components['pangowin32'].system_libs.append('gdi32')

        if self.options.with_cairo:
            self.cpp_info.components['pangocairo'].libs = ['pangocairo-1.0']
            self.cpp_info.components['pangocairo'].names['pkg_config'] = 'pangocairo'
            self.cpp_info.components['pangocairo'].requires = ['pango_']
            if self.options.with_freetype:
                self.cpp_info.components['pangocairo'].requires.append('pangoft2')
            if self.settings.os == "Windows":
                self.cpp_info.components['pangocairo'].requires.append('pangowin32')
                self.cpp_info.components['pangocairo'].system_libs.append('gdi32')
            self.cpp_info.components['pangocairo'].includedirs = [os.path.join(self.package_folder, "include", "pango-1.0")]

        self.env_info.PATH.append(os.path.join(self.package_folder, 'bin'))

    def package_id(self):
        if not self.info.options["glib"].get_safe("shared"):
            self.info.requires["glib"].full_package_mode()
        if not self.info.options["harfbuzz"].get_safe("shared"):
            self.info.requires["harfbuzz"].full_package_mode()
        if self.info.options.with_cairo and not self.info.options["cairo"].get_safe("shared"):
            self.info.requires["cairo"].full_package_mode()