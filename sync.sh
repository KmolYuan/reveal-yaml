REVEAL_VER="4.0.2"
wget "https://registry.npmjs.org/reveal.js/-/reveal.js-${REVEAL_VER}.tgz" -O reveal.tgz
tar -xvzf reveal.tgz
rm -f reveal.tgz
find ./package -name "*.esm.js" -delete
find ./package -name "plugin.js" -delete
cp -r package/dist static/reveal.js
cp -r package/plugin static/plugin
rm -fr package

CDNJS="https://cdnjs.cloudflare.com/ajax/libs"
JQUERY="${CDNJS}/jquery/3.5.1"
ACE="${CDNJS}/ace/1.4.12"
JSYAML="${CDNJS}/js-yaml/3.14.0"

mkdir static/js
mkdir static/ace
wget "${JQUERY}/jquery.min.js" -P static/js
wget "${ACE}/ace.min.js" -P static/ace
wget "${ACE}/ext-searchbox.min.js" -P static/ace
wget "${ACE}/ext-whitespace.min.js" -P static/ace
wget "${ACE}/ext-language_tools.min.js" -P static/ace
wget "${ACE}/mode-yaml.min.js" -P static/ace
wget "${ACE}/theme-chrome.min.js" -P static/ace
wget "${ACE}/theme-monokai.min.js" -P static/ace
wget "${JSYAML}/js-yaml.min.js" -P static/ace
