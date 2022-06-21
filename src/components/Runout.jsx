import {
  ArrowCircleLeftRounded,
  ArrowCircleRightRounded,
  ArrowLeft,
  ArrowRight,
  SkipNextRounded,
  SkipPreviousRounded,
} from "@mui/icons-material";
import {
  Button,
  Stack,
  Typography,
  ButtonGroup,
  IconButton,
} from "@mui/material";
import React, { useEffect } from "react";
import Footer from "./Footer";

const Runout = () => {
  const inputRef = React.useRef();
  const videoRef = React.useRef();
  const [source, setSource] = React.useState();

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    const url = URL.createObjectURL(file);
    setSource(url);
  };

  let frameTime = 1 / 45;

  useEffect(() => {
    window.addEventListener("keydown", function (event) {
      if (event.key == "ArrowLeft") {
        videoRef.current.currentTime = Math.max(
          0,
          videoRef.current.currentTime - frameTime
        );
      } else if (event.key == "ArrowRight") {
        videoRef.current.currentTime = Math.min(
          videoRef.current.duration,
          videoRef.current.currentTime + frameTime
        );
      }
    });
  }, []);

  //   //handle frame
  const handleFrame = (direction) => {
    if (direction == "forward") {
      videoRef.current.currentTime = Math.min(
        videoRef.current.duration,
        videoRef.current.currentTime + frameTime
      );
    } else if (direction == "5forward") {
      videoRef.current.currentTime = Math.min(
        videoRef.current.duration,
        videoRef.current.currentTime + 5 * frameTime
      );
    } else if (direction == "backward") {
      videoRef.current.currentTime = Math.max(
        0,
        videoRef.current.currentTime - frameTime
      );
    } else if (direction == "5backward") {
      videoRef.current.currentTime = Math.max(
        0,
        videoRef.current.currentTime - 5 * frameTime
      );
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
        Run Out Check
      </Typography>
      <Typography
        variant="body1"
        textAlign="center"
        paddingBottom={3}
        color="secondary"
      >
        Video from Leg Umpire's point of view would be the best !
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
            <Stack direction="row" sx={{ flexWrap: "wrap" }} spacing={0.7}>
              <Button
                variant="contained"
                color="primary"
                size="small"
                startIcon={<SkipPreviousRounded />}
                onClick={() => handleFrame("5backward")}
              />

              <Button
                variant="contained"
                color="primary"
                size="small"
                sx={{ textTransform: 'none'}}
                onClick={() => handleFrame("backward")}
              >
                Prev. Frame
              </Button>
              <Button
                variant="contained"
                color="primary"
                size="small"
                sx={{ textTransform: 'none'}}
                onClick={() => handleFrame("forward")}
              >
                Next Frame
              </Button>

              <Button
                variant="contained"
                color="primary"
                size="small"
                endIcon={<SkipNextRounded />}
                onClick={() => handleFrame("5forward")}
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

export default Runout;
