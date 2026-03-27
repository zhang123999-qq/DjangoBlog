"""
.gitignore生成器工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class GitignoreGeneratorForm(forms.Form):
    """gitignore生成器表单"""
    project_types = forms.MultipleChoiceField(
        label='项目类型',
        choices=[
            ('python', 'Python'),
            ('django', 'Django'),
            ('node', 'Node.js'),
            ('react', 'React'),
            ('vue', 'Vue.js'),
            ('java', 'Java'),
            ('spring', 'Spring Boot'),
            ('go', 'Go'),
            ('rust', 'Rust'),
            ('dotnet', '.NET/C#'),
            ('php', 'PHP'),
            ('laravel', 'Laravel'),
            ('ruby', 'Ruby'),
            ('rails', 'Rails'),
            ('swift', 'Swift/iOS'),
            ('android', 'Android'),
            ('flutter', 'Flutter'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True
    )
    ides = forms.MultipleChoiceField(
        label='IDE/编辑器',
        choices=[
            ('vscode', 'VS Code'),
            ('idea', 'IntelliJ IDEA'),
            ('pycharm', 'PyCharm'),
            ('webstorm', 'WebStorm'),
            ('sublime', 'Sublime Text'),
            ('vim', 'Vim'),
            ('emacs', 'Emacs'),
            ('eclipse', 'Eclipse'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    os_types = forms.MultipleChoiceField(
        label='操作系统',
        choices=[
            ('macos', 'macOS'),
            ('windows', 'Windows'),
            ('linux', 'Linux'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    extras = forms.MultipleChoiceField(
        label='额外选项',
        choices=[
            ('secrets', '敏感文件(.env, credentials)'),
            ('docker', 'Docker'),
            ('terraform', 'Terraform'),
            ('database', '数据库文件'),
            ('logs', '日志文件'),
            ('backup', '备份文件'),
            ('archives', '压缩包'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )


# gitignore模板
GITIGNORE_TEMPLATES = {
    'python': '''
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
''',
    'django': '''
# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
media/

# Static files
staticfiles/
static/CACHE/
''',
    'node': '''
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
package-lock.json
yarn.lock

# Build output
dist/
build/
.cache/

# Environment
.env
.env.local
.env.*.local

# Logs
logs/
*.log

# Runtime data
pids/
*.pid
*.seed
*.pid.lock
''',
    'react': '''
# React / Next.js
.next/
out/
.nuxt/

# Production
build/

# Misc
.DS_Store
Thumbs.db
''',
    'vue': '''
# Vue
.vite/
.nuxt/
.output/
.cache/

# Production
dist/
''',
    'java': '''
# Compiled class file
*.class

# Log file
*.log

# Package Files
*.jar
*.war
*.nar
*.ear
*.zip
*.tar.gz
*.rar

# Maven
target/
pom.xml.tag
pom.xml.releaseBackup
pom.xml.versionsBackup
pom.xml.next
release.properties
dependency-reduced-pom.xml
buildNumber.properties
.mvn/timing.properties
.mvn/wrapper/maven-wrapper.jar

# Gradle
.gradle/
build/
!gradle/wrapper/gradle-wrapper.jar
''',
    'spring': '''
# Spring Boot
*.jar
*.war
target/

# Application properties
application-dev.properties
application-prod.properties
''',
    'go': '''
# Binaries for programs and plugins
*.exe
*.exe~
*.dll
*.so
*.dylib

# Test binary
*.test

# Output of the go coverage tool
*.out

# Dependency directories
vendor/

# Go workspace file
go.work
''',
    'rust': '''
# Generated files
target/

# Cargo lock for libraries
Cargo.lock

# Backup files
**/*.rs.bk
''',
    'dotnet': '''
# Build results
[Dd]ebug/
[Rr]elease/
x64/
x86/
[Aa][Rr][Mm]/
[Aa][Rr][Mm]64/
bld/
[Bb]in/
[Oo]bj/

# Visual Studio
.vs/
*.suo
*.user
*.userosscache
*.sln.docstates

# NuGet
packages/
*.nupkg
*.snupkg
project.lock.json
project.fragment.lock.json
artifacts/
''',
    'php': '''
# Composer
vendor/
composer.lock

# PHP
*.log
*.cache

# Laravel
/storage/
/bootstrap/cache/
''',
    'laravel': '''
# Laravel
/storage/*.key
/storage/
/bootstrap/cache/
.env
Homestead.yaml
Homestead.json
/.vagrant
.phpunit.result.cache
''',
    'ruby': '''
# Bundler
/.bundle
/vendor/bundle

# Gem
*.gem

# Rails
/log/*
/tmp/*
!/log/.keep
!/tmp/.keep

# Environment
.env
.env.local
.env.*.local
''',
    'rails': '''
# Rails
/public/assets
/public/packs
/public/packs-test
/node_modules
/yarn.lock
/yarn-error.log
/storage
''',
    'swift': '''
# Xcode
build/
DerivedData/
*.pbxuser
!default.pbxuser
*.mode1v3
!default.mode1v3
*.mode2v3
!default.mode2v3
*.perspectivev3
!default.perspectivev3
xcuserdata/
*.xccheckout
*.moved-aside
*.xcuserstate
*.xcscmblueprint

# Swift Package Manager
.build/
.swiftpm/

# CocoaPods
Pods/

# Carthage
Carthage/Build/
''',
    'android': '''
# Built application files
*.apk
*.aar
*.ap_
*.aab

# Files for the ART/Dalvik VM
*.dex

# Generated files
bin/
gen/
out/
release/

# Gradle files
.gradle/
build/

# Local configuration file
local.properties

# Proguard folder
proguard/

# Android Studio
*.iml
.idea/
''',
    'flutter': '''
# Flutter/Dart
.dart_tool/
.flutter-plugins
.flutter-plugins-dependencies
.packages
.pub-cache/
.pub/
build/

# Android
**/android/**/gradle-wrapper.jar
**/android/.gradle
**/android/captures/
**/android/gradlew
**/android/gradlew.bat
**/android/local.properties
**/android/**/GeneratedPluginRegistrant.java

# iOS
**/ios/**/*.mode1v3
**/ios/**/*.mode2v3
**/ios/**/*.moved-aside
**/ios/**/*.pbxuser
**/ios/**/*.perspectivev3
''',
    # IDE
    'vscode': '''
# VS Code
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json
*.code-workspace
''',
    'idea': '''
# IntelliJ IDEA
.idea/
*.iml
*.ipr
*.iws
out/
''',
    'pycharm': '''
# PyCharm
.idea/
*.iml
''',
    'webstorm': '''
# WebStorm
.idea/
*.iml
''',
    'sublime': '''
# Sublime Text
*.tmlanguage.cache
*.tmPreferences.cache
*.stTheme.cache
*.sublime-workspace
''',
    'vim': '''
# Vim
*.swp
*.swo
*~
.*.sw[a-z]
*.un~
Session.vim
.netrwhist
''',
    'emacs': r'''
# Emacs
*~
\#*\#
/.emacs.desktop
/.emacs.desktop.lock
*.elc
auto-save-list
tramp
.\#*
''',
    'eclipse': '''
# Eclipse
.settings/
.classpath
.project
.metadata/
bin/
tmp/
''',
    # OS
    'macos': '''
# macOS
.DS_Store
.AppleDouble
.LSOverride
._*
.Spotlight-V100
.Trashes
''',
    'windows': '''
# Windows
Thumbs.db
Thumbs.db:encryptable
ehthumbs.db
ehthumbs_vista.db
*.stackdump
[Dd]esktop.ini
$RECYCLE.BIN/
''',
    'linux': '''
# Linux
*~
.fuse_hidden*
.directory
.Trash-*
.nfs*
''',
    # Extras
    'secrets': '''
# Secrets
.env
.env.*
*.pem
*.key
credentials.json
secrets.json
.secrets/
''',
    'docker': '''
# Docker
.docker/
docker-compose.override.yml
''',
    'terraform': '''
# Terraform
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
.terraformrc
terraform.rc
''',
    'database': '''
# Database
*.db
*.sqlite
*.sqlite3
*.sql
*.mdb
''',
    'logs': '''
# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
''',
    'backup': '''
# Backup
*.bak
*.backup
*.old
*.orig
''',
    'archives': '''
# Archives
*.zip
*.tar
*.tar.gz
*.rar
*.7z
*.gz
''',
}


class GitignoreGeneratorTool(BaseTool):
    """gitignore生成器工具"""
    name = ".gitignore生成器"
    slug = "gitignore-generator"
    description = "根据项目类型自动生成.gitignore文件"
    icon = "git-alt"
    category = ToolCategory.GENERATE
    form_class = GitignoreGeneratorForm
    template_name = "tools/gitignore_generator.html"

    def handle(self, request, form):
        project_types = form.cleaned_data.get('project_types', [])
        ides = form.cleaned_data.get('ides', [])
        os_types = form.cleaned_data.get('os_types', [])
        extras = form.cleaned_data.get('extras', [])

        # 合并所有选择
        all_selections = project_types + ides + os_types + extras

        # 生成gitignore内容
        result_parts = []
        used_templates = []

        for selection in all_selections:
            if selection in GITIGNORE_TEMPLATES:
                template = GITIGNORE_TEMPLATES[selection]
                if template not in result_parts:
                    # 添加注释头
                    result_parts.append(f'\n# === {self._get_name(selection)} ===')
                    result_parts.append(template.strip())
                    used_templates.append(self._get_name(selection))

        result = '\n'.join(result_parts)

        # 清理多余空行
        result = '\n'.join(line for line in result.split('\n') if line.strip() or line == '')

        return {
            'result': result.strip(),
            'used_templates': used_templates,
            'stats': {
                'total_selections': len(all_selections),
                'line_count': len(result.strip().split('\n')),
            }
        }

    def _get_name(self, key):
        """获取友好名称"""
        names = {
            'python': 'Python',
            'django': 'Django',
            'node': 'Node.js',
            'react': 'React',
            'vue': 'Vue.js',
            'java': 'Java',
            'spring': 'Spring Boot',
            'go': 'Go',
            'rust': 'Rust',
            'dotnet': '.NET/C#',
            'php': 'PHP',
            'laravel': 'Laravel',
            'ruby': 'Ruby',
            'rails': 'Rails',
            'swift': 'Swift/iOS',
            'android': 'Android',
            'flutter': 'Flutter',
            'vscode': 'VS Code',
            'idea': 'IntelliJ IDEA',
            'pycharm': 'PyCharm',
            'webstorm': 'WebStorm',
            'sublime': 'Sublime Text',
            'vim': 'Vim',
            'emacs': 'Emacs',
            'eclipse': 'Eclipse',
            'macos': 'macOS',
            'windows': 'Windows',
            'linux': 'Linux',
            'secrets': 'Secrets',
            'docker': 'Docker',
            'terraform': 'Terraform',
            'database': 'Database',
            'logs': 'Logs',
            'backup': 'Backup',
            'archives': 'Archives',
        }
        return names.get(key, key)
