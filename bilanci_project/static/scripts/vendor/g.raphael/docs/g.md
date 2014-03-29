# g.raphael.js

This file contains the tooltips for Element and Paper. Tooltips include tag, drop, blob, popup, flag, label. It also has functions that can modify the element brightness. Last of which is a set of common properties for chart.

## Tooltips

### Element.popup
Puts the context Element in a 'popup' tooltip. Can also be used on sets.

#### Parameters
 - dir (string) location of Element relative to the tail: `'down'`, `'left'`, `'up'` [default], or `'right'`.
 - size (number) amount of bevel/padding around the Element, as well as half the width and height of the tail [default: `5`]
 - x (number) x coordinate of the popup's tail [default: Element's `x` or `cx`]
 - y (number) y coordinate of the popup's tail [default: Element's `y` or `cy`]

#### Returns
(object) path element of the popup

#### Usage
    paper.circle(50, 50, 5).attr({
        stroke: "#fff",
        fill: "0-#c9de96-#8ab66b:44-#398235"
    }).popup();


### Element.tag
Puts the context Element in a 'tag' tooltip. Can also be used on sets.

#### Parameters
 - angle (number) angle of orientation in degrees [default: `0`]
 - r (number) radius of the loop [default: `5`]
 - x (number) x coordinate of the center of the tag loop [default: Element's `x` or `cx`]
 - y (number) y coordinate of the center of the tag loop [default: Element's `x` or `cx`]

#### Returns
 = (object) path element of the tag

#### Usage
    paper.circle(50, 50, 15).attr({
        stroke: "#fff",
        fill: "0-#c9de96-#8ab66b:44-#398235"
    }).tag(60);


### Element.drop
Puts the context Element in a 'drop' tooltip. Can also be used on sets.

#### Parameters
 - angle (number) angle of orientation in degrees [default: `0`]
 - x (number) x coordinate of the drop's point [default: Element's `x` or `cx`]
 - y (number) y coordinate of the drop's point [default: Element's `x` or `cx`]

#### Returns
(object) path element of the drop

#### Usage
    paper.circle(50, 50, 8).attr({
        stroke: "#fff",
        fill: "0-#c9de96-#8ab66b:44-#398235"
    }).drop(60);


### Element.flag
Puts the context Element in a 'flag' tooltip. Can also be used on sets.

#### Parameters
 - angle (number) angle of orientation in degrees [default: `0`]
 - x (number) x coordinate of the flag's point [default: Element's `x` or `cx`]
 - y (number) y coordinate of the flag's point [default: Element's `x` or `cx`]

#### Returns
 = (object) path element of the flag

#### Usage
    paper.circle(50, 50, 10).attr({
        stroke: "#fff",
        fill: "0-#c9de96-#8ab66b:44-#398235"
    }).flag(60);

### Element.label
Puts the context Element in a 'label' tooltip. Can also be used on sets.

#### Returns
(object) path element of the label.

#### Usage
    paper.circle(50, 50, 10).attr({
        stroke: "#fff",
        fill: "0-#c9de96-#8ab66b:44-#398235"
    }).label();

### Element.blob
Puts the context Element in a 'blob' tooltip. Can also be used on sets.

#### Parameters
 - angle (number) angle of orientation in degrees [default: `0`]
 - x (number) x coordinate of the blob's tail [default: Element's `x` or `cx`]
 - y (number) y coordinate of the blob's tail [default: Element's `x` or `cx`]

#### Returns
(object) path element of the blob

#### Usage
    paper.circle(50, 50, 8).attr({
        stroke: "#fff",
        fill: "0-#c9de96-#8ab66b:44-#398235"
    }).blob(60);

### Paper.label
Puts the given `text` into a 'label' tooltip. The text is given a default style according to @g.txtattr. See @Element.label

#### Parameters
 - x (number) x coordinate of the center of the label
 - y (number) y coordinate of the center of the label
 - text (string) text to place inside the label

#### Returns
(object) set containing the label path and the text element

#### Usage
    paper.label(50, 50, "$9.99");

### Paper.popup
Puts the given `text` into a 'popup' tooltip. The text is given a default style according to @g.txtattr. See @Element.popup

*Note*: The `dir` parameter has changed from g.Raphael 0.4.1 to 0.5. The options `0`, `1`, `2`, and `3` has been changed to `'down'`, `'left'`, `'up'`, and `'right'` respectively.

#### Parameters
 - x (number) x coordinate of the popup's tail
 - y (number) y coordinate of the popup's tail
 - text (string) text to place inside the popup
 - dir (string) location of the text relative to the tail: `'down'`, `'left'`, `'up'` [default], or `'right'`.
 - size (number) amount of padding around the Element [default: `5`]

#### Returns
(object) set containing the popup path and the text element

#### Usage
    paper.popup(50, 50, "$9.99", 'down');

### Paper.tag
Puts the given text into a 'tag' tooltip. The text is given a default style according to @g.txtattr. See @Element.tag

#### Parameters
 - x (number) x coordinate of the center of the tag loop
 - y (number) y coordinate of the center of the tag loop
 - text (string) text to place inside the tag
 - angle (number) angle of orientation in degrees [default: `0`]
 - r (number) radius of the loop [default: `5`]

#### Returns
(object) set containing the tag path and the text element

#### Usage
    paper.tag(50, 50, "$9.99", 60);

### Paper.flag
Puts the given `text` into a 'flag' tooltip. The text is given a default style according to @g.txtattr. See @Element.flag

#### Parameters
 - x (number) x coordinate of the flag's point
 - y (number) y coordinate of the flag's point
 - text (string) text to place inside the flag
 - angle (number) angle of orientation in degrees [default: `0`]

#### Returns
(object) set containing the flag path and the text element

#### Usage
    paper.flag(50, 50, "$9.99", 60);

### Paper.drop
Puts the given text into a 'drop' tooltip. The text is given a default style according to @g.txtattr. See @Element.drop

#### Parameters
 - x (number) x coordinate of the drop's point
 - y (number) y coordinate of the drop's point
 - text (string) text to place inside the drop
 - angle (number) angle of orientation in degrees [default: `0`]

#### Returns
(object) set containing the drop path and the text element

#### Usage
    paper.drop(50, 50, "$9.99", 60);

### Paper.blob
Puts the given text into a 'blob' tooltip. The text is given a default style according to @g.txtattr. See @Element.blob

#### Parameters
 - x (number) x coordinate of the blob's tail
 - y (number) y coordinate of the blob's tail
 - text (string) text to place inside the blob
 - angle (number) angle of orientation in degrees [default: `0`]

#### Returns
(object) set containing the blob path and the text element

#### Usage
    paper.blob(50, 50, "$9.99", 60);

### Element.lighter
Makes the context element lighter by increasing the brightness and reducing the saturation by a given factor. Can be called on Sets.

#### Parameters
 - times (number) adjustment factor [default: `2`]

#### Returns
(object) Element

#### Usage
    paper.circle(50, 50, 20).attr({
        fill: "#ff0000",
        stroke: "#fff",
        "stroke-width": 2
    }).lighter(6);


## Brightness functions on the Element prototype

### Element.darker
Makes the context element darker by decreasing the brightness and increasing the saturation by a given factor. Can be called on Sets.

#### Parameters
 - times (number) adjustment factor [default: `2`]

#### Returns
(object) Element

#### Usage
    paper.circle(50, 50, 20).attr({
        fill: "#ff0000",
        stroke: "#fff",
        "stroke-width": 2
    }).darker(6);

### Element.resetBrightness
Resets brightness and saturation levels to their original values. See @Element.lighter and @Element.darker. Can be called on Sets.

#### Returns
(object) Element

#### Usage
    paper.circle(50, 50, 20).attr({
        fill: "#ff0000",
        stroke: "#fff",
        "stroke-width": 2
    }).lighter(6).resetBrightness();

## Chart prototype for storing common functions

### g.shim
An attribute object that charts will set on all generated shims (shims being the invisible objects that mouse events are bound to)

#### Default value
    { stroke: 'none', fill: '#000', 'fill-opacity': 0 }

### g.txtattr
An attribute object that charts and tooltips will set on any generated text

#### Default value
    { font: '12px Arial, sans-serif', fill: '#fff' }

### g.colors
An array of color values that charts will iterate through when drawing chart data values.


## Written by ##

Kenny Shen, www.northpole.sg.
