window.InventoryScanner = (function(){
  let codeReader = null;
  let active = false;

  async function attach({videoId, startBtnId, stopBtnId, onCode}){
    const video = document.getElementById(videoId);
    const startBtn = document.getElementById(startBtnId);
    const stopBtn = document.getElementById(stopBtnId);

    codeReader = new ZXing.BrowserMultiFormatReader();

    async function start(){
      if(active) return;
      active = true;
      const devices = await ZXing.BrowserCodeReader.listVideoInputDevices();
      const deviceId = devices?.[0]?.deviceId;

      codeReader.decodeFromVideoDevice(deviceId, video, (result, err) => {
        if(result){
          const code = result.getText();
          onCode && onCode(code);
        }
      });
    }

    function stop(){
      active = false;
      if(codeReader){
        codeReader.reset();
      }
    }

    startBtn && startBtn.addEventListener("click", start);
    stopBtn && stopBtn.addEventListener("click", stop);
  }

  return { attach };
})();
