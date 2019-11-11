var el = x => document.getElementById(x);

function showPicker() {
  el("file-input").click();
}

//some codes to compress/resize is taken from:
//https://zocada.com/compress-resize-images-javascript-browser/

function showPicked(input) {
  const width = 400;

  const fileName = input.files[0].name;
  el("upload-label").innerHTML = fileName;
  var reader = new FileReader();
  reader.onload = function(readerEvent) {
    el("image-picked").src = readerEvent.target.result;
    el("image-picked").className = "";
	 
    var img = new Image();
    img.onload = function(imageEvent) {
      const elem = document.createElement('canvas');
      const scaleFactor = width / img.width;
      elem.width = width;
      elem.height = img.height * scaleFactor;
      const ctx = elem.getContext('2d');
      // img.width and img.height will contain the original dimensions
      ctx.drawImage(img, 0, 0, width, img.height * scaleFactor);
      const dataUrl = ctx.canvas.toDataURL(img, 'image/jpeg', 1);
      //el("resized-image").className = "";
      el("resized-image").src = dataUrl;
      //var resizedImage = dataURLToBlob(dataUrl);
      //el("resized-Image") = resizedImage;
      //ctx.canvas.toBlob((blob) => {
      //  const file = new File([blob], fileName, {
      //                  type: 'image/jpeg',
      //                  lastModified: Date.now()
      //  });
      //}, 'image/jpeg', 1);
    }
    img.src = readerEvent.target.result;
    reader.onerror = error => console.log(error);

  };
  reader.readAsDataURL(input.files[0]);
}

//https://stackoverflow.com/questions/23945494/use-html5-to-resize-an-image-before-upload
/* Utility function to convert a canvas to a BLOB */
var dataURLToBlob = function(dataURL) {
    var BASE64_MARKER = ';base64,';
    if (dataURL.indexOf(BASE64_MARKER) == -1) {
        var parts = dataURL.split(',');
        var contentType = parts[0].split(':')[1];
        var raw = parts[1];

        return new Blob([raw], {type: contentType});
    }

    var parts = dataURL.split(BASE64_MARKER);
    var contentType = parts[0].split(':')[1];
    var raw = window.atob(parts[1]);
    var rawLength = raw.length;

    var uInt8Array = new Uint8Array(rawLength);

    for (var i = 0; i < rawLength; ++i) {
        uInt8Array[i] = raw.charCodeAt(i);
    }

    return new Blob([uInt8Array], {type: contentType});
}
/* End Utility function to convert a canvas to a BLOB      */

function analyze() {
  var uploadFiles = el("file-input").files;
  if (uploadFiles.length !== 1) alert("Please select a file to analyze!");

  el("analyze-button").innerHTML = "Analyzing...";
  el("result-label").innerHTML = "Waiting...";
  var xhr = new XMLHttpRequest();
  var loc = window.location;
  xhr.open("POST", `${loc.protocol}//${loc.hostname}:${loc.port}/analyze`,
    true);
  xhr.onerror = function() {
    alert(xhr.responseText);
  };
  xhr.onload = function(e) {
    if (this.readyState === 4) {
      var response = JSON.parse(e.target.responseText);
      el("result-label").innerHTML = `Result = ${response["result"]}`;
    }
    el("analyze-button").innerHTML = "Analyze";
  };

  var fileData = new FormData();
  if (el("original").checked)
    fileData.append("image", el("resized-image").src);
  else
    fileData.append("file", uploadFiles[0]);
  xhr.send(fileData);
}

