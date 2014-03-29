# g.bar.js #

## Requirements ##

 + raphael.js
 + g.raphael.js
 + g.bar.js
 
## Overview ##

Creates a bar chart.

## Parameters ##

**1. x** number **X coordinate of the centre**

**2. y** number **Y coordinate of the centre**

**3. width** number **width**

**4. height** number **height**

**5. values** array of numbers **Values for your bars.**

**5. opts** object **Options (more info soon.)**

_opts_

**type**

Values are,

    + "round"
    + "sharp"
    + "soft"
    + "square"
    
Defaults to "square" if type is not specified.

**stacked**

Values are,

    + true
    + false
    
Defaults to false. Use this to stack your bars instead of displaying them side by side.

**gutter**

Values given as a string, denoting %. E.g. "40%"

Defaults to "20%". For horizontal barcharts, this is calculated as,

    bargutter = Math.floor(barheight * gutter / 100)
    
e.g. if my height was 220, and I had 4 bars, then my barheight is calculated as,

    Math.floor(height / (len * (100 + gutter) + gutter) * 100); // where len is 4 and height is 220, and if not specified, gutter is 20
    
then according to the above, my bargutter = 8px.
    
    
## Methods ##

**1. .hover(fin, fout)** - fin/fout: **callbacks to trigger when mouse hovers in and out respectively over the bars.**

## Usage ##

Create a bar chart,


    // bare bones
    var barchart = r.g.barchart(_params);
    // example
    var barchart = r.g.barchart(10, 10, 300, 220, [[30, 20, 10]]);
    // horizontal barchart 
    var hbarchart = r.g.hbarchart(10, 10, 300, 220, [[30, 20, 10]]);
    
    
Create a stacked bar chart,


    // example
    var barchart = r.g.barchart(10, 10, 300, 220, [[30, 20, 10], [44, 66, 88]], {stacked:true});
    
    
Attach hover event to piechart,


    // example
    r.g.barchart.hover(function() {
        this.bar.attr({fill: "#333"}); 
    }, function() {
        this.bar.attr({fill: "#666"});
    });

## Others ##

N/A

## Written by ##

Kenny Shen, www.northpole.sg.