# Requirements

+ Python 3.6+

Install modules:

```bash
pip install -r requirements.txt
```

# Startup

```bash
python app.py
# Without SSH
python -m flask app.py
```

# Generate SSL key

```bash
openssl genrsa 2048 > localhost.key
chmod 400 localhost.key
openssl req -new -x509 -nodes -sha256 -days 365 -key localhost.key -out localhost.crt
```

# Build Static Page

```bash
python build_frozen.py
```

# YAML Template

```yaml
title: Title
nav:
  - title: Title
    doc: |
      Author: Me
    sub:
      - title: What a Good Slide!
      - title: Next Good Slide!
        doc: |
          $$
          x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
          $$

  - title: Next Chapter
    doc: |
      + list
      + list
      + list
```
