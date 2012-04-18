jQuery(
  function() {
    jQuery.ajaxSetup({'cache': false});

    var cgi_path = "../cgi-bin/";
    var url_param_strings = location.search.substring(1).split("&");
    var projid = "";
    var task = "features";
    for(var c = 0; c < url_param_strings.length; c++) {
      var pos = url_param_strings[c].indexOf("=");
      if(pos == -1) continue;
      var name = url_param_strings[c].substring(0, pos);
      if(name == "projid")  {
        projid = decodeURIComponent(url_param_strings[c].substring(pos + 1));
      }
      else if(name == "task") {
        task = decodeURIComponent(url_param_strings[c].substring(pos + 1));
      }
    }
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
                       { verb: "get", task: "lines", projid: projid, pageid: href}, page_callback);
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
    //add one.

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
    }


    $('#image_container').click(on_imagecontainer_click);


    function on_submit_click(event) {
      var line_positions = [];
      $("div.linehere").each(function(index, element) {
        var line;
        if(element.id)
          line = +(element.id.substr(5));
        else {
          var height_i = $("#image").height();
          var image_position = $("#image").offset();
          line = Math.floor(($(element).offset().top - image_position.top + $(element).height() / 2) * 10000 / height_i);
        }
        line_positions.push(line);});
      line_positions.sort(function(a, b) {return a - b; });
      var json_lines = JSON.stringify(line_positions);
      jQuery.post(cgi_path + "command.py", {verb:"save", task: "lines", lines:json_lines,
                                            projid: projid, pageid: pageid}, submit_callback);
    }
    $('#submit').click(on_submit_click);


    function submit_callback(ob, status) {
      jQuery.getJSON(cgi_path + "command.py",
      {verb:"list", task: "lines", type: "res", projid: projid},
                     list_callback);
      jQuery.getJSON(cgi_path + "command.py",
      {verb:"list", task: "lines", type: "done", projid: projid},
                     list_callback);
    }

    function list_callback(ob, status) {
      var list_type = ob[0];
      var listing = ob[1];
      var content;
      if(listing.length == 0)
          content = $("<p>None</p>");
      else {
        content = ($("<table/>"));
        for(var c = 0; c < listing.length; c++) {
          content.append($("<tr><td><a href='" +
                           listing[c][0] + "'>" +
                           listing[c][0] + "</a></td><td>" +
                           listing[c][1] + "</td></tr>"));
        }
      }
      $('#' + list_type).replaceWith($("<div id='" + list_type + "'/>").append(content));
    }

    //kick things off
    submit_callback();


  });