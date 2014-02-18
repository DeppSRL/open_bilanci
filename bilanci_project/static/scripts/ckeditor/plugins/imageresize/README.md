ImageResize Plugin for CKEditor 4
=================================

Created by ALL-INKL.COM - Neue Medien Münnich - 27. Jan 2014

This Plugin provides a small image processor. You can limit the size of images
directly on the client without upload images on your server. Big images will be
resized automatically on paste.


## Installation

 1. Download the plugin from http://ckeditor.com/addon/imageresize

 2. Extract (decompress) the downloaded file into the plugins folder of your
	CKEditor installation.
	Example: http://example.com/ckeditor/plugins/imageresize

 3. Enable the plugin by using the extraPlugins configuration setting.
	Example: CKEDITOR.config.extraPlugins = "imageresize";


## Documentation

 // Resize all images in a node:
	CKEDITOR.plugins.imageresize.resizeAll(
		CKEditor Instance,
		(node) parent container,
		(integer) max-width,
		(integer) max-height
	);

 // Resize one image:
	CKEDITOR.plugins.imageresize.resize(
		CKEditor Instance,
		(node) image,
		(integer) max-width,
		(integer) max-height
	);

 // Detect browser support:
 // returns boolean true or false
	CKEDITOR.plugins.imageresize.support();
