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
  host: http://localhost:5000
  origins:
    - www.my-website.com
    - internal-server.de:8000
secrets:
  - "ev,*uVoGK#A@HRx=3_6)#e"
```

The `host` determines the current host the service is running on. This is used when building the access urls for clients
after the pdf has been rendered. The list of `origins` defines all allowed origins to access the service from. The list
of `secrets` defines a set of api keys to authenticate requests.

## Usage

The latex-render-service exposes two endpoints.

### Render endpoint

```python
import requests

r = requests.post(
    'http://localhost:5000/render/example-template',
    data={
        'name': 'Finn',
        'dogs': [
            'Corgi',
            'Husky',
            'Dachshund',
        ]
    },
    headers={
        'Authorization': 'ev,*uVoGK#A@HRx=3_6)#e'
    }
)

print('Rendered pdf is at', r.text)
```

The render endpoint only accepts post-requests and returns the url of the rendered pdf file. To render a template, the
endpoint receives the id of the template, i.e. the filename of the latex file without the `.tex` extension and a json
context payload. The context payload is used during the rendering of the template to provide the data for jinja. After
the rendering is done, the url of the rendered file is returned from the endpoint.

The rendered pdfs are cached and can be accessed multiple times. The cache is based on a hash of the id of the template
and the context data. That means, that if a template is rendered twice, with the same context data, no real rendering
takes place the second time the render endpoint is called. Only the cached data is returned.

Because the caching is based on template ids and context data, a change in the templates themselves is not reflected in
the hash. This leads to the requirement of cleaning the cache, i.e. deleting all items, when the templates change.

### Cache endpoint

The cache endpoint provides a cached file if it was previously rendered.
The endpoint supports a query parameter for the filename of the returned pdf.

```
http://localhost:5000/cache/9f1e9b738bc220312dcd12274ee23a27d78aa624.pdf?filename=favorite%20dogs.pdf
```

## Backup Cache

The rendering results are cached based on the uploaded data and the name of the template.

You can mount the directory `/app/cache` as a volume to back up the rendered Pdfs. Please be aware, that you need to
clean your cache, after you have updated the templates.

## docker-compose

```yaml
version: "3"
services:
  lrs:
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