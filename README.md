# About

The latex-render-service is a service to render LaTeX templates based on api requests.

# Setup

## Templates

You can store all your LaTeX templates in a single directory. The filenames of your templates are used when accessing
them via the api. For rendering your templates the jinja2 engine is used. There have been adjustments to the jinja2
keywords to fit the overall LaTeX style.

The process and style for templating is based upon the works
of [Brad Erickson](http://eosrei.net/articles/2015/11/latex-templates-python-and-jinja2-generate-pdfs).

```latex
\documentclass[12pt]{article}

\begin{document}

    \section*{\VAR{name}s Favorite Dogs}

    \begin{itemize}
        \BLOCK{ for dog in dogs }
        \item \VAR{dog}
        \BLOCK{ endfor }
    \end{itemize}

\end{document}
```

This template can now be called with a json payload.

```json
{
  "name": "Finn",
  "dogs": [
    "Corgi",
    "Husky",
    "Dachshund"
  ]
}
```

## Config

```yaml
# ./conf/conf.yml
server:
  origins:
    - www.my-website.com
    - internal-server.de:8000
secrets:
  - "ev,*uVoGK#A@HRx=3_6)#e"
```

The list of `origins` defines all allowed origins to access the service from.
The list of `secrets` defines a set of api keys to authenticate requests.

## Backup Cache

The rendering results are cached based on the uploaded data and the name of the template.

You can mount the directory `/app/cache` as a volume to back up the rendered Pdfs. Please be aware, that you need to
clean your cache, after you have updated the templates.

## docker-compose

```yaml
version: "3"
services:
  pdfutil:
    build:
      context: .
    restart: always
    ports:
      - "5000:5000"
    volumes:
      - ./conf:/app/conf
      - ./cache:/app/cache
      - ./templates:/app/templates
```