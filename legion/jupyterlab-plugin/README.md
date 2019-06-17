# legion

Integration with Legion (Cluster and Local modes)


## Prerequisites

* JupyterLab (version 0.35)
* legion-sdk python package

## Installation

```bash
jupyter labextension install jupyter_legion
```

## Development

For a development install (requires npm version 4 or later), do the following in the repository directory:

```bash
npm install
npm run build
jupyter labextension link .
```

To rebuild the package and the JupyterLab app:

```bash
npm run build
jupyter lab build
```

## Third-party components

### Icons
* cloud - https://www.iconfinder.com/icons/211653/cloud_icon
* gears - https://www.iconfinder.com/icons/1608900/gears_icon
* lock - https://www.iconfinder.com/icons/1608769/lock_icon