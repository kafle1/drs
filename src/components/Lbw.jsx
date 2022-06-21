import SkipPreviousIcon from "@mui/icons-material/SkipPrevious";
import SkipNextIcon from "@mui/icons-material/SkipNext";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";
import { Button, ButtonGroup, Stack, Typography } from "@mui/material";
import React from "react";
import Footer from "./Footer";

const Lbw = () => {
  const inputRef = React.useRef();
  const videoRef = React.useRef();
  const [source, setSource] = React.useState();

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    const url = URL.createObjectURL(file);
    setSource(url);
  };

  const handleButton = (type) => {
    if (type == "play") {
      videoRef.current.playbackRate = 0.2;
      videoRef.current.muted = true;
      videoRef.current.play();
    } else if (type == "pause") {
      videoRef.current.pause();
    } else if (type == "backward") {
      videoRef.current.currentTime = videoRef.current.currentTime - 3;
    } else if (type == "forward") {
      videoRef.current.currentTime = videoRef.current.currentTime + 3;
    }
  };
  return (
    <div>
      <Typography
        textAlign="center"
        paddingTop={2}
        variant="h4"
        color="initial"
      >
        DRS System
      </Typography>
      <Typography textAlign="center" variant="h5" color="primary">
        LBW Check
      </Typography>
      <Typography
        variant="body1"
        textAlign="center"
        paddingBottom={3}
        color="secondary"
      >
        Video from Umpire's point of view would be the best ! (Hawk-eye feature
        coming soon!)
      </Typography>

      <Stack
        paddingBottom={3}
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
        }}
        spacing={3}
      >
        {source && (
          <>
            <video ref={videoRef} id="video" src={source} width="100%">
              <source src={source} type="video" />
            </video>
            <Stack direction="row" sx={{flexWrap: "wrap"}} spacing={0.7}>
              <Button
                variant="contained"
                color="primary"
                size="small"
                startIcon={<SkipPreviousIcon />}
                onClick={() => handleButton("backward")}
              />
              <Button
                variant="contained"
                color="primary"
                size="small"
                startIcon={<PlayArrowIcon />}
                onClick={() => handleButton("play")}
              >
                Play
              </Button>
              <Button
                variant="contained"
                color="primary"
                size="small"
                startIcon={<PauseIcon />}
                onClick={() => handleButton("pause")}
              >
                Pause
              </Button>
              <Button
                variant="contained"
                color="primary"
                size="small"
                startIcon={<SkipNextIcon />}
                onClick={() => handleButton("forward")}
              />
            </Stack>
          </>
        )}

        {!source && (
          <>
            <input
              ref={inputRef}
              accept="video/*"
              style={{ display: "none" }}
              id="raised-button-file"
              onChange={handleFileChange}
              type="file"
            />
            <label htmlFor="raised-button-file">
              <Button variant="contained" component="span">
                Upload Video
              </Button>
            </label>
          </>
        )}
      </Stack>
      <Footer />
    </div>
  );
};

export default Lbw;
