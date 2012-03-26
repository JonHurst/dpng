jQuery(
  function() {
    jQuery.ajaxSetup({'cache': false});

    var cgi_path = "../cgi-bin/";
    var projid = $('body').attr('id');//projid id is body tag id for now
    var pageid;
    var image;
    var lines;

    //if a pagepicker descendent with an href is clicked, treat it as a pageid: load image
    //and add divs to represent lines
    function on_pagepicker_click(event) {
      event.preventDefault();
      var href = $(event.target).attr('href');
      if(href) {
        pageid = href;
        jQuery.getJSON(cgi_path + "command.py",
                       { verb:"get", projid: projid, pageid: href}, page_callback);
      }
    }

    function page_callback(ob, status) {
      image = ob[3][1];
      lines = ob[4];
      load_image(image);
    }

    $('#pagepicker').click(on_pagepicker_click);

    function load_image(url, pos) {
      url = url || "../images/blank.png";
      var img = $("<img />").attr({'src': url, 'alt': pos, 'id': "image"});
      if ( img.get(0).complete || img.get(0).readyState === 4 ) {
        image_load_handler({currentTarget: img.get(0)});
      }
      else {
        img.load(image_load_handler);
      }
    }

    function image_load_handler(event) {
      var target = event.currentTarget;
      var pos = target.getAttribute('alt');
      $('#image').eq(pos).replaceWith(target);
      $('.linehere').remove();
      var height = $("#image").height();
      var divs = [];
      for(var c = 0; c < lines.length; c++) {
        divs[c] = $("<div class=\"linehere\"/>");
        divs[c].insertAfter("#image");
        var div_position = $("#image").offset();
        div_position.top += (lines[c] * height / 10000) - divs[c].height() / 2;
        divs[c].offset(div_position);
        divs[c].attr("id", "line_" + lines[c]);
        }
    }

    //if a line is clicked, remove it; if the image is clicked where there is no line div,
    //add one. Send changes to server immediately.
    function on_linehere_click(div, line_positions) {
      var line;
      if(this.id)
        line = +(this.id.substr(5));
      else
        var height_i = $("#image").height();
        var image_position = $("#image").offset();

        line = Math.floor((div.offset().top - image_position.top + div.height() / 2) * 10000 / height_i);
      line_positions.push(line);
    }


    function on_imagecontainer_click(event) {
      if(event.target.className == "linehere")
        $(event.target).remove();
      else {
        var div = $("<div class=\"linehere\"/>");
        div.insertAfter("#image");
        var div_position = $("#image").offset();
        div_position.top = event.pageY - 3;
        div.offset(div_position);
        }
      var line_positions = [];
      $("div.linehere").each(function() {on_linehere_click($(this), line_positions);});
      line_positions.sort(function(a, b) {return a - b; });
      var json_lines = JSON.stringify(line_positions);
      jQuery.post(cgi_path + "command.py", {verb:"lines", lines:json_lines,
                                            projid: projid, pageid: pageid});
    }


    $('#image_container').click(on_imagecontainer_click);


    //load the pagepicker to start things off
    $('#pagepicker_tables').load(cgi_path + "command.py",
                                 {verb:"list", projid: projid, user: "lines"});

  });