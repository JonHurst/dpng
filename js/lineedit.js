jQuery(
  function() {
    jQuery.ajaxSetup({'cache': false});

    var ajax_interface = "../cgi-bin/lineedit.py";
    var url_param_strings = location.search.substring(1).split("&");
    var projid = "";
    for(var c = 0; c < url_param_strings.length; c++) {
      var pos = url_param_strings[c].indexOf("=");
      if(pos == -1) continue;
      var name = url_param_strings[c].substring(0, pos);
      if(name == "projid")  {
        projid = decodeURIComponent(url_param_strings[c].substring(pos + 1));
      }
    }
    var pageid;
    var image;
    var lines;


    (function() /*controls*/ {
       function samples_change(event, ui) {
         $("#sample_text").val(
           "Samples per line: " + ui.value);
       }
       $("#sample_fraction").slider(
         {min:10, max:50,
          change: samples_change,
          slide: samples_change});
       $("#sample_fraction").slider("value", 16);
       function thresholds_change( event, ui ) {
         $("#threshold_range").val(
           "Thresholds: " + ui.values[0] + " - " + ui.values[1]);
       }
       $("#thresholds").slider(
         {range: true, min: 0, max: 100, values: [0, 0],
          change: thresholds_change,
          slide: thresholds_change});
       $("#thresholds").slider("values", [60, 80]);
       $("#calibrate").click(
         function() {
           jQuery.getJSON(
             ajax_interface,
             {verb:"calibrate", projid:projid, pageid:pageid,
              samples: $("#sample_fraction").slider("value")},
             function(ob) {
               $("#thresholds").slider("values", ob);
             });
         });
     })();

    //if a pagepicker descendent with an href is clicked, treat it as a pageid: load image
    //and add divs to represent lines
    $('#pagepicker').click(
      function(event) {
        event.preventDefault();
        var href = $(event.target).attr('href');
        if(href) {
          pageid = href;
          jQuery.getJSON(
            ajax_interface,
            { verb: "get_lines", projid: projid, pageid: href},
            function(ob) {
              lines = ob;
              var url = ajax_interface + "?" + 
                jQuery.param({verb: "get_image", projid: projid, pageid: pageid});
              var img = $("<img />").attr({'src': url, 'alt': "", 'id': "image"});
              if ( img.get(0).complete || img.get(0).readyState === 4 ) {
                image_load_handler({currentTarget: img.get(0)});
              }
              else {
                img.load(image_load_handler);
              }
            });
        }
      });


    function image_load_handler(event) {
      var target = event.currentTarget;
      var pos = target.getAttribute('alt');
      $('#image').replaceWith(target);
      refresh_lines();
    }


    function refresh_lines() {
      if(lines == undefined) return;
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
      $('.linehere').width($('#image').width());
    }
    $(window).resize(refresh_lines);


    $('#recalc').click(
      function() {
        jQuery.getJSON(
          ajax_interface,
          { verb: "calc_lines", projid: projid, pageid: pageid,
            black_threshold: $("#thresholds").slider("values", 0),
            white_threshold: $("#thresholds").slider("values", 1),
            samples: $("#sample_fraction").slider("value")},
            function(ob) {
              lines = ob;
              refresh_lines();
            });
      });


    //if a line div is clicked, remove it; if the image is clicked
    //where there is no line div, add one.
    $('#image_container').click(
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
      });


      function on_drop_first(ev) {
          var first;
          var min_pos = Number.MAX_VALUE;
          var line_divs = $('.linehere');
          for(var c = 0; c < line_divs.length; c++) {
              var pos = $(line_divs[c]).position();
              if(pos.top < min_pos) {
                  min_pos = pos.top;
                  first = c;
              }
          }
          $(line_divs[first]).remove();
      }
      $('#drop_first').click(on_drop_first);


      function on_drop_last(ev) {
          var last = 0;
          var max_pos = 0;
          var line_divs = $('.linehere');
          for(var c = 0; c < line_divs.length; c++) {
              var pos = $(line_divs[c]).position();
              if(pos.top > max_pos) {
                  max_pos = pos.top;
                  last = c;
              }
          }
          $(line_divs[last]).remove();
      }
      $('#drop_last').click(on_drop_last);


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
      jQuery.post(ajax_interface, {verb:"save", task: "lines", lines:json_lines,
                                            projid: projid, pageid: pageid}, submit_callback);
    }
    $('#submit').click(on_submit_click);


    function list(ob, status) {
      function page_list(id_list) {
        var content;
        if(id_list.length == 0)
          content = $("<p>None</p>");
        else {
          content = ($("<div class='page_list'/>"));
          for(var c = 0; c < id_list.length; c++) {
            content.append($("<a class='page_ref' href='" +
                             id_list[c] + "'>" +
                             id_list[c] + "</a>"));
          }
        }
        return content;
      }
      jQuery.getJSON(
        ajax_interface,
        {verb:"list_lines", projid: projid},
        function(ob) {
          $('#todo').empty().append(page_list(ob[0]));
          $('#done').empty().append(page_list(ob[1]));
        });
    }

    list();
  });