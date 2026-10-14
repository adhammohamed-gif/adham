import React from 'react';
import {AbsoluteFill, CanvasImage, Composition, Easing, Interactive, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

const GREEN = '#00552d';
const RED = '#b82924';
const INK = '#153b2b';
const PAPER = '#f6f8f4';
const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const, easing: ease};
const font = 'Arial, Helvetica, sans-serif';

const Icon: React.FC<{kind: 'play' | 'book' | 'pages'; size?: number}> = ({kind, size = 48}) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" stroke={GREEN} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    {kind === 'play' ? <><rect x="6" y="8" width="36" height="31" rx="8"/><path d="M21 17L31 23.5L21 30Z" fill={GREEN} stroke="none"/></> : null}
    {kind === 'book' ? <><path d="M24 12C15 6 6 11 6 11V36C6 36 15 31 24 37C33 31 42 36 42 36V11C42 11 33 6 24 12Z"/><path d="M24 12V37M12 17L18 18M30 18L36 17"/></> : null}
    {kind === 'pages' ? <><rect x="12" y="7" width="26" height="33" rx="5"/><path d="M7 15V37Q7 44 14 44M19 16H31M19 23H31M19 30H27"/></> : null}
  </svg>
);

const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return <AbsoluteFill style={{background: PAPER, overflow: 'hidden'}}>
    <AbsoluteFill style={{backgroundImage: 'radial-gradient(#9bb8a525 1.4px, transparent 1.4px)', backgroundSize: '38px 38px'}}/>
    <div style={{position: 'absolute', width: 1100, height: 1100, borderRadius: '50%', top: -660, right: -360, background: 'radial-gradient(circle, #dcebdd80 0%, #f6f8f400 68%)'}}/>
    <svg width="1920" height="1080" style={{position: 'absolute', left: 0, top: 0, opacity: .55}}>
      <path d="M-20 370 H130 Q200 370 200 440 V740 Q200 800 260 800 H370" fill="none" stroke="#cbddd0" strokeWidth="2" strokeDasharray="1000" strokeDashoffset={interpolate(frame, [0, 2.4 * fps], [1000, 0], clamp)}/>
      <path d="M1940 350 H1785 Q1720 350 1720 415 V700 Q1720 765 1655 765 H1560" fill="none" stroke="#cbddd0" strokeWidth="2" strokeDasharray="1000" strokeDashoffset={interpolate(frame, [.3 * fps, 2.7 * fps], [1000, 0], clamp)}/>
      <circle cx="200" cy="475" r="8" fill={GREEN} opacity={interpolate(frame, [0, 1 * fps], [0, .7], clamp)}/>
      <circle cx="1720" cy="555" r="7" fill={RED} opacity={interpolate(frame, [1 * fps, 2 * fps], [0, .7], clamp)}/>
      <circle cx="370" cy="800" r="5" fill={RED}/>
      <circle cx="1560" cy="765" r="5" fill={GREEN}/>
    </svg>
    <div style={{position: 'absolute', inset: 38, border: '1px solid #dfe8df', borderRadius: 30}}/>
  </AbsoluteFill>;
};

const Logo: React.FC<{top?: number; width?: number; delay?: number}> = ({top = 145, width = 720, delay = .2}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return <Interactive.Div name="SAJA Connect logo" premountFor={fps} style={{position: 'absolute', top, left: (1920 - width) / 2, width, opacity: interpolate(frame, [delay * fps, (delay + .8) * fps], [0, 1], clamp), translate: interpolate(frame, [delay * fps, (delay + .8) * fps], ['0px 25px', '0px 0px'], clamp)}}>
    <CanvasImage src={staticFile('saja-connect-logo.png')} premountFor={fps} style={{width: '100%'}}/>
  </Interactive.Div>;
};

const FeatureCard: React.FC<{label: string; kind: 'play' | 'book' | 'pages'; left: number; delay: number}> = ({label, kind, left, delay}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return <Interactive.Div name={label} premountFor={fps} style={{position: 'absolute', left, top: 720, width: 454, height: 126, borderRadius: 26, background: '#ffffff', border: '1px solid #dfe7dd', boxShadow: '0 20px 65px #25472d09', display: 'flex', alignItems: 'center', gap: 21, padding: '0 29px', boxSizing: 'border-box', opacity: interpolate(frame, [delay * fps, (delay + .75) * fps], [0, 1], clamp), translate: interpolate(frame, [delay * fps, (delay + .75) * fps], ['0px 55px', '0px 0px'], clamp)}}>
    <div style={{width: 65, height: 65, background: '#eaf2e8', borderRadius: 18, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}><Icon kind={kind}/></div>
    <div style={{fontSize: 33, fontWeight: 600, color: INK, letterSpacing: -.8, lineHeight: 1.2}}>{label.split(' ')[0]}<br/>{label.split(' ').slice(1).join(' ')}</div>
    <div style={{position: 'absolute', top: 19, right: 19, height: 5, width: 5, borderRadius: '50%', background: RED}}/>
  </Interactive.Div>;
};

export const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return <AbsoluteFill style={{fontFamily: font}}>
    <Background/>
    <Logo top={122} width={740}/>
    <Interactive.Div name="Intro headline" premountFor={fps} style={{position: 'absolute', top: 398, left: 200, width: 1520, textAlign: 'center', color: INK, fontSize: 106, lineHeight: 1.04, fontWeight: 700, letterSpacing: -5.5, opacity: interpolate(frame, [1.05 * fps, 1.8 * fps], [0, 1], clamp), translate: interpolate(frame, [1.05 * fps, 1.8 * fps], ['0px 40px', '0px 0px'], clamp)}}>
      Learning beyond<br/><span style={{color: GREEN}}>the conference.</span>
    </Interactive.Div>
    <FeatureCard label="Conference sessions" kind="play" left={251} delay={2.5}/>
    <FeatureCard label="Medical education" kind="book" left={733} delay={2.75}/>
    <FeatureCard label="Concise summaries" kind="pages" left={1215} delay={3}/>
    <Interactive.Div name="Website address" premountFor={fps} style={{position: 'absolute', top: 939, left: 0, width: '100%', fontSize: 35, color: GREEN, textAlign: 'center', letterSpacing: -.4, opacity: interpolate(frame, [3.8 * fps, 4.5 * fps], [0, 1], clamp)}}>sajaconnect.com</Interactive.Div>
    <AbsoluteFill style={{background: PAPER, opacity: interpolate(frame, [7.4 * fps, 8 * fps], [0, 1], clamp)}}/>
  </AbsoluteFill>;
};

export const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return <AbsoluteFill style={{fontFamily: font}}>
    <Background/>
    <Logo top={108} width={665} delay={.1}/>
    <Interactive.Div name="Outro headline" premountFor={fps} style={{position: 'absolute', top: 385, left: 200, width: 1520, textAlign: 'center', fontSize: 105, fontWeight: 700, letterSpacing: -5, color: INK, opacity: interpolate(frame, [.9 * fps, 1.6 * fps], [0, 1], clamp), translate: interpolate(frame, [.9 * fps, 1.6 * fps], ['0px 35px', '0px 0px'], clamp)}}>Continue your learning.</Interactive.Div>
    <Interactive.Div name="What is available" premountFor={fps} style={{position: 'absolute', top: 523, left: 300, width: 1320, fontSize: 45, lineHeight: 1.45, color: '#53705b', textAlign: 'center', letterSpacing: -.9, opacity: interpolate(frame, [1.5 * fps, 2.2 * fps], [0, 1], clamp)}}>Explore conference sessions and medical education<br/>on SAJA Connect.</Interactive.Div>
    <Interactive.Div name="Website call to action" premountFor={fps} style={{position: 'absolute', top: 709, left: 618, width: 684, height: 110, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 37, background: GREEN, color: 'white', borderRadius: 25, fontSize: 45, fontWeight: 600, letterSpacing: -1, boxShadow: '0 25px 50px #00552d19', opacity: interpolate(frame, [2.3 * fps, 3 * fps], [0, 1], clamp), translate: interpolate(frame, [2.3 * fps, 3 * fps], ['0px 28px', '0px 0px'], clamp)}}>
      sajaconnect.com
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none" stroke="#e4f0e4" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round"><path d="M5 18H30M21 9L30 18L21 27"/></svg>
    </Interactive.Div>
    <Interactive.Div name="Contact email" premountFor={fps} style={{position: 'absolute', top: 887, left: 0, width: '100%', color: '#68806a', fontSize: 31, textAlign: 'center', opacity: interpolate(frame, [3.2 * fps, 3.9 * fps], [0, 1], clamp)}}>info@sajaconnect.com</Interactive.Div>
  </AbsoluteFill>;
};

export const Review: React.FC = () => {
  const {fps} = useVideoConfig();
  return <AbsoluteFill>
    <Sequence name="Intro sample" durationInFrames={8 * fps} premountFor={fps}><Intro/></Sequence>
    <Sequence name="Outro sample" from={8 * fps} durationInFrames={8 * fps} premountFor={fps}><Outro/></Sequence>
  </AbsoluteFill>;
};

export const MyComposition = () => <>
  <Composition id="SAJA-Connect-Intro" component={Intro} durationInFrames={240} fps={30} width={1920} height={1080}/>
  <Composition id="SAJA-Connect-Outro" component={Outro} durationInFrames={240} fps={30} width={1920} height={1080}/>
  <Composition id="SAJA-Connect-Review" component={Review} durationInFrames={480} fps={30} width={1920} height={1080}/>
</>;
