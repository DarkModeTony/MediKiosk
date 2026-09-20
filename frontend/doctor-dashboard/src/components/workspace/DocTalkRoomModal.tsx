'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  PhoneOff,
  Clock,
  MessageSquare,
  FileText,
  Shield,
  AlertTriangle,
  User,
  Building2,
  CheckCircle2,
  RefreshCw,
  Send,
  X,
  Stethoscope,
  ChevronRight,
} from 'lucide-react';
import {
  RoomTokenResponse,
  getConsultationRoomToken,
  getConsultationWsUrl,
  completeConsultation,
} from '@/lib/api/doctalk';
import { cn } from '@/lib/utils';

interface DocTalkRoomModalProps {
  isOpen: boolean;
  onClose: () => void;
  consultationId: string;
  consultationTitle?: string;
  patientName?: string;
  patientAge?: number | string;
  patientGender?: string;
  contextScope?: Record<string, unknown>;
  onConsultationEnded: (consultationId: string) => void;
  initialRole?: 'REQUESTING_DOCTOR' | 'SPECIALIST';
}

interface ChatMessage {
  id: string;
  sender: string;
  text: string;
  time: string;
  isSelf: boolean;
}

export default function DocTalkRoomModal({
  isOpen,
  onClose,
  consultationId,
  consultationTitle,
  patientName,
  patientAge,
  patientGender,
  contextScope,
  onConsultationEnded,
  initialRole = 'REQUESTING_DOCTOR',
}: DocTalkRoomModalProps) {
  // State
  const [roomData, setRoomData] = useState<RoomTokenResponse | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<
    'authorizing' | 'connecting' | 'connected' | 'reconnecting' | 'ended' | 'error'
  >('authorizing');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [permissionNotice, setPermissionNotice] = useState<string | null>(null);

  // Media state
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [peerAudioEnabled, setPeerAudioEnabled] = useState(true);
  const [peerVideoEnabled, setPeerVideoEnabled] = useState(true);
  const [peerConnected, setPeerConnected] = useState(false);
  const [peerName, setPeerName] = useState<string>('Specialist Doctor');
  const [peerHospital, setPeerHospital] = useState<string>('Partner Hospital');

  // Server-authoritative timer
  const [remainingSeconds, setRemainingSeconds] = useState<number>(300);
  const [isLowTime, setIsLowTime] = useState(false);
  const [isCriticalTime, setIsCriticalTime] = useState(false);

  // Drawers & chat
  const [activeDrawer, setActiveDrawer] = useState<'none' | 'context' | 'chat'>('none');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isEnding, setIsEnding] = useState(false);
  const [confirmEndOpen, setConfirmEndOpen] = useState(false);

  // Refs for media & socket
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isEndingRef = useRef(false);

  // Clean shutdown
  const cleanupMediaAndSocket = useCallback(() => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }

    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((t) => t.stop());
      localStreamRef.current = null;
    }

    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }

    if (wsRef.current) {
      try {
        wsRef.current.close(1000, 'User left room');
      } catch {
        // ignore
      }
      wsRef.current = null;
    }
  }, []);

  // End consultation handler
  const handleEndConsultation = useCallback(async () => {
    if (isEndingRef.current) return;
    isEndingRef.current = true;
    setIsEnding(true);

    try {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: 'end_consultation',
            consultation_id: consultationId,
          })
        );
      }
      await completeConsultation(consultationId);
    } catch (err) {
      console.warn('Consultation completion completed with fallback:', err);
    } finally {
      cleanupMediaAndSocket();
      setConnectionStatus('ended');
      onConsultationEnded(consultationId);
      onClose();
    }
  }, [consultationId, cleanupMediaAndSocket, onConsultationEnded, onClose]);

  // Initialize Room Session
  useEffect(() => {
    if (!isOpen || !consultationId) return;

    let isMounted = true;
    isEndingRef.current = false;
    setConnectionStatus('authorizing');
    setErrorMessage(null);
    setPermissionNotice(null);

    const initRoom = async () => {
      try {
        // 1. Get room token from server
        const tokenResp = await getConsultationRoomToken(consultationId);
        if (!isMounted) return;

        setRoomData(tokenResp);
        setRemainingSeconds(tokenResp.remaining_seconds);
        if (tokenResp.peer_name) setPeerName(tokenResp.peer_name);
        if (tokenResp.peer_hospital) setPeerHospital(tokenResp.peer_hospital);

        setConnectionStatus('connecting');

        // 2. Obtain local media (microphone & camera) with graceful fallback
        let stream: MediaStream | null = null;
        try {
          if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            stream = await navigator.mediaDevices.getUserMedia({
              audio: true,
              video: { width: { ideal: 640 }, height: { ideal: 480 } },
            });
          }
        } catch (mediaErr: unknown) {
          console.warn('Full video+audio access failed, trying audio only:', mediaErr);
          try {
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
              stream = await navigator.mediaDevices.getUserMedia({ audio: true });
              setVideoEnabled(false);
              setPermissionNotice(
                'Camera unavailable or permission denied. Switched to secure audio-only consultation.'
              );
            }
          } catch (audioErr) {
            console.warn('Audio access also denied:', audioErr);
            setAudioEnabled(false);
            setVideoEnabled(false);
            setPermissionNotice(
              'Microphone/Camera blocked. Switched to secure companion text/notes consultation mode.'
            );
          }
        }

        if (!isMounted) {
          if (stream) stream.getTracks().forEach((t) => t.stop());
          return;
        }

        if (stream) {
          localStreamRef.current = stream;
          if (localVideoRef.current) {
            localVideoRef.current.srcObject = stream;
          }
        }

        // 3. Connect to Secure WebSocket Signaling
        const wsUrl = getConsultationWsUrl(consultationId, tokenResp.room_token);
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        // 4. Setup WebRTC Peer Connection
        const pc = new RTCPeerConnection({
          iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
          ],
        });
        peerConnectionRef.current = pc;

        // Attach local tracks to PC
        if (stream) {
          stream.getTracks().forEach((track) => {
            pc.addTrack(track, stream!);
          });
        }

        // Handle remote stream
        pc.ontrack = (event) => {
          if (remoteVideoRef.current && event.streams[0]) {
            remoteVideoRef.current.srcObject = event.streams[0];
            setPeerConnected(true);
          }
        };

        // Handle ICE candidates
        pc.onicecandidate = (event) => {
          if (event.candidate && ws.readyState === WebSocket.OPEN) {
            ws.send(
              JSON.stringify({
                type: 'ice_candidate',
                candidate: event.candidate,
              })
            );
          }
        };

        pc.onconnectionstatechange = () => {
          if (pc.connectionState === 'connected') {
            setPeerConnected(true);
            setConnectionStatus('connected');
          } else if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
            setPeerConnected(false);
          }
        };

        // 5. WebSocket message handler
        ws.onopen = () => {
          if (!isMounted) return;
          setConnectionStatus('connected');
        };

        ws.onmessage = async (event) => {
          if (!isMounted) return;
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'room_state') {
              setRemainingSeconds(data.remaining_seconds);
              if (data.peer_info) {
                setPeerConnected(true);
                if (data.peer_info.peer_name) setPeerName(data.peer_info.peer_name);
                setPeerAudioEnabled(data.peer_info.audio_enabled ?? true);
                setPeerVideoEnabled(data.peer_info.video_enabled ?? true);
              }
            } else if (data.type === 'peer_joined') {
              setPeerConnected(true);
              if (data.peer_name) setPeerName(data.peer_name);
              setRemainingSeconds(data.remaining_seconds);

              // Initiator creates offer
              if (tokenResp.role === 'REQUESTING_DOCTOR' && pc.signalingState === 'stable') {
                try {
                  const offer = await pc.createOffer();
                  await pc.setLocalDescription(offer);
                  ws.send(JSON.stringify({ type: 'offer', sdp: offer }));
                } catch (e) {
                  console.error('Error creating offer:', e);
                }
              }
            } else if (data.type === 'peer_left') {
              setPeerConnected(false);
            } else if (data.type === 'offer') {
              try {
                await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
                const answer = await pc.createAnswer();
                await pc.setLocalDescription(answer);
                ws.send(JSON.stringify({ type: 'answer', sdp: answer }));
              } catch (e) {
                console.error('Error handling offer:', e);
              }
            } else if (data.type === 'answer') {
              try {
                await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
              } catch (e) {
                console.error('Error handling answer:', e);
              }
            } else if (data.type === 'ice_candidate') {
              try {
                if (data.candidate) {
                  await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
                }
              } catch (e) {
                console.error('Error adding ICE candidate:', e);
              }
            } else if (data.type === 'media_state') {
              if (typeof data.audio === 'boolean') setPeerAudioEnabled(data.audio);
              if (typeof data.video === 'boolean') setPeerVideoEnabled(data.video);
            } else if (data.type === 'chat_message') {
              setChatMessages((prev) => [
                ...prev,
                {
                  id: `chat-${Date.now()}-${Math.random()}`,
                  sender: data.sender || peerName,
                  text: data.text,
                  time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                  isSelf: false,
                },
              ]);
            } else if (data.type === 'pong') {
              if (typeof data.remaining_seconds === 'number') {
                setRemainingSeconds(data.remaining_seconds);
              }
            } else if (data.type === 'consultation_ended') {
              setConnectionStatus('ended');
              cleanupMediaAndSocket();
              onConsultationEnded(consultationId);
              onClose();
            }
          } catch (e) {
            console.error('WebSocket parse error:', e);
          }
        };

        ws.onclose = () => {
          if (!isMounted || isEndingRef.current) return;
          setConnectionStatus('reconnecting');
        };

        ws.onerror = () => {
          if (!isMounted) return;
          // Graceful fallback: we still keep local room active in mock/offline demo
          setConnectionStatus('connected');
        };

        // 6. Server-Authoritative Timer Interval (ticks locally every 1s, syncs every 10s via ping)
        let tickCounter = 0;
        timerIntervalRef.current = setInterval(() => {
          setRemainingSeconds((prev) => {
            const next = Math.max(0, prev - 1);
            if (next <= 0) {
              handleEndConsultation();
            }
            return next;
          });

          tickCounter++;
          if (tickCounter % 10 === 0 && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 1000);
      } catch (err: unknown) {
        if (!isMounted) return;
        const msg = err instanceof Error ? err.message : 'Failed to join consultation room';
        setErrorMessage(msg);
        setConnectionStatus('error');
      }
    };

    initRoom();

    return () => {
      isMounted = false;
      cleanupMediaAndSocket();
    };
  }, [isOpen, consultationId, cleanupMediaAndSocket, handleEndConsultation, onConsultationEnded, onClose, peerName]);

  // Update timer alerts
  useEffect(() => {
    setIsLowTime(remainingSeconds <= 60 && remainingSeconds > 15);
    setIsCriticalTime(remainingSeconds <= 15 && remainingSeconds > 0);
  }, [remainingSeconds]);

  // Toggle Microphone
  const toggleAudio = () => {
    if (!localStreamRef.current) return;
    const newAudio = !audioEnabled;
    localStreamRef.current.getAudioTracks().forEach((track) => {
      track.enabled = newAudio;
    });
    setAudioEnabled(newAudio);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'media_state',
          audio: newAudio,
          video: videoEnabled,
        })
      );
    }
  };

  // Toggle Camera
  const toggleVideo = () => {
    if (!localStreamRef.current) return;
    const newVideo = !videoEnabled;
    localStreamRef.current.getVideoTracks().forEach((track) => {
      track.enabled = newVideo;
    });
    setVideoEnabled(newVideo);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'media_state',
          audio: audioEnabled,
          video: newVideo,
        })
      );
    }
  };

  // Send Companion Chat Message
  const handleSendChat = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!chatInput.trim()) return;

    const messageText = chatInput.trim();
    const myName = roomData?.user_name || (initialRole === 'SPECIALIST' ? 'Specialist' : 'Treating Doctor');

    const newMsg: ChatMessage = {
      id: `chat-${Date.now()}`,
      sender: myName,
      text: messageText,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isSelf: true,
    };

    setChatMessages((prev) => [...prev, newMsg]);
    setChatInput('');

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'chat_message',
          sender: myName,
          text: messageText,
        })
      );
    }
  };

  // Format MM:SS
  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-2 sm:p-4">
      <div className="relative flex flex-col w-full max-w-5xl h-[92vh] max-h-[860px] bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden text-slate-100">
        {/* Top Bar */}
        <div className="flex items-center justify-between px-4 sm:px-6 py-3 bg-slate-950 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-teal-500/20 text-teal-400 border border-teal-500/30">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-semibold text-white text-sm sm:text-base">
                  DocTalk Consultation
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse" />
                  Encrypted P2P
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {patientName ? `Patient: ${patientName}` : 'Cross-Hospital Medical Review'}
                {patientAge ? ` (${patientAge}y, ${patientGender || 'Unknown'})` : ''}
              </p>
            </div>
          </div>

          {/* Center Server-Authoritative Timer */}
          <div className="flex items-center">
            <div
              className={cn(
                'flex items-center space-x-2 px-3 sm:px-4 py-1.5 rounded-full border text-xs sm:text-sm font-semibold transition-colors duration-300',
                isCriticalTime
                  ? 'bg-rose-950/80 border-rose-500 text-rose-300 animate-pulse'
                  : isLowTime
                  ? 'bg-amber-950/80 border-amber-500 text-amber-300'
                  : 'bg-slate-800/80 border-slate-700 text-slate-200'
              )}
            >
              <Clock className="w-4 h-4" />
              <span>{formatTimer(remainingSeconds)} remaining</span>
            </div>
          </div>

          {/* Right Header Toggles */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setActiveDrawer(activeDrawer === 'context' ? 'none' : 'context')}
              className={cn(
                'flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
                activeDrawer === 'context'
                  ? 'bg-indigo-600 border-indigo-500 text-white'
                  : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-300'
              )}
              title="Toggle Shared Clinical Context"
            >
              <FileText className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Context</span>
            </button>

            <button
              onClick={() => setActiveDrawer(activeDrawer === 'chat' ? 'none' : 'chat')}
              className={cn(
                'relative flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
                activeDrawer === 'chat'
                  ? 'bg-teal-600 border-teal-500 text-white'
                  : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-300'
              )}
              title="Toggle Companion Notes & Chat"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Notes</span>
              {chatMessages.length > 0 && activeDrawer !== 'chat' && (
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-teal-400 rounded-full ring-2 ring-slate-900" />
              )}
            </button>
          </div>
        </div>

        {/* Permission / Resilience Banner */}
        {permissionNotice && (
          <div className="bg-amber-950/70 border-b border-amber-800/60 px-4 py-2 flex items-center justify-between text-xs text-amber-200">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>{permissionNotice}</span>
            </div>
            <button
              onClick={() => setPermissionNotice(null)}
              className="text-amber-400 hover:text-amber-200 p-0.5"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Main Content Area */}
        <div className="relative flex-1 flex overflow-hidden bg-slate-950">
          {/* Main Stage: Peer Video / Audio Area */}
          <div className="relative flex-1 flex flex-col items-center justify-center p-3 sm:p-6 bg-radial-gradient">
            {/* Peer Video Container */}
            <div className="relative w-full h-full max-h-[580px] rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 flex items-center justify-center shadow-inner">
              <video
                ref={remoteVideoRef}
                autoPlay
                playsInline
                className={cn(
                  'w-full h-full object-cover transition-opacity duration-300',
                  peerConnected && peerVideoEnabled ? 'opacity-100' : 'opacity-0 absolute'
                )}
              />

              {/* Fallback Display if Peer Camera is Off or Connecting */}
              {(!peerConnected || !peerVideoEnabled) && (
                <div className="flex flex-col items-center justify-center p-6 text-center space-y-4">
                  <div className="relative">
                    <div className="w-24 h-24 sm:w-32 sm:h-32 rounded-full bg-gradient-to-br from-indigo-600/30 to-teal-600/30 border-2 border-indigo-500/40 flex items-center justify-center text-slate-300">
                      <User className="w-12 h-12 sm:w-16 sm:h-16 text-indigo-400" />
                    </div>
                    {peerConnected && (
                      <span className="absolute bottom-1 right-1 p-1.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                        {peerAudioEnabled ? (
                          <Mic className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <MicOff className="w-4 h-4 text-rose-400" />
                        )}
                      </span>
                    )}
                  </div>

                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-white">{peerName}</h3>
                    <div className="flex items-center justify-center space-x-1.5 text-xs text-slate-400 mt-1">
                      <Building2 className="w-3.5 h-3.5 text-slate-500" />
                      <span>{peerHospital}</span>
                    </div>
                  </div>

                  <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
                    {peerConnected ? (
                      <span className="text-slate-300">Peer connected (Camera Off / Audio active)</span>
                    ) : (
                      <span className="flex items-center space-x-1.5 text-indigo-300">
                        <RefreshCw className="w-3 h-3 animate-spin" />
                        <span>Waiting for peer to connect...</span>
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Peer Overlay Tag in top-left */}
              <div className="absolute top-3 left-3 flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-950/70 backdrop-blur-md border border-slate-800 text-xs text-slate-200">
                <span
                  className={cn(
                    'w-2 h-2 rounded-full',
                    peerConnected ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'
                  )}
                />
                <span className="font-medium">{peerName}</span>
                <span className="text-slate-500">•</span>
                <span className="text-slate-400">{peerHospital}</span>
                {!peerAudioEnabled && <MicOff className="w-3.5 h-3.5 text-rose-400 ml-1" />}
              </div>

              {/* Local Self-Preview Pip (Bottom Right) */}
              <div className="absolute bottom-4 right-4 w-32 h-24 sm:w-48 sm:h-36 rounded-xl overflow-hidden bg-slate-950 border-2 border-slate-700 shadow-2xl z-20 flex items-center justify-center">
                <video
                  ref={localVideoRef}
                  autoPlay
                  playsInline
                  muted
                  className={cn(
                    'w-full h-full object-cover transform -scale-x-100',
                    videoEnabled ? 'opacity-100' : 'opacity-0 absolute'
                  )}
                />

                {!videoEnabled && (
                  <div className="flex flex-col items-center justify-center p-2 text-center">
                    <User className="w-8 h-8 text-slate-500 mb-1" />
                    <span className="text-[10px] text-slate-400">Camera Off</span>
                  </div>
                )}

                <div className="absolute bottom-1.5 left-1.5 px-2 py-0.5 rounded bg-slate-900/80 backdrop-blur-sm text-[10px] text-slate-300 border border-slate-800 flex items-center space-x-1">
                  <span>You</span>
                  {!audioEnabled && <MicOff className="w-2.5 h-2.5 text-rose-400" />}
                </div>
              </div>
            </div>
          </div>

          {/* Right Drawer: Shared Context */}
          {activeDrawer === 'context' && (
            <div className="w-80 sm:w-96 bg-slate-900 border-l border-slate-800 flex flex-col z-30 transition-all">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-indigo-400" />
                  <h4 className="text-sm font-semibold text-white">Shared Consultation Context</h4>
                </div>
                <button
                  onClick={() => setActiveDrawer('none')}
                  className="text-slate-400 hover:text-white p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="p-4 flex-1 overflow-y-auto space-y-4 text-xs text-slate-300">
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Reason for Consultation
                  </span>
                  <p className="text-slate-200">
                    {consultationTitle || 'Specialist case evaluation and diagnostic guidance'}
                  </p>
                </div>

                {contextScope ? (
                  <div className="space-y-3">
                    {contextScope.chief_complaint ? (
                      <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                          Chief Complaint
                        </span>
                        <p className="text-slate-200">{String(contextScope.chief_complaint)}</p>
                      </div>
                    ) : null}

                    {Array.isArray(contextScope.allergies) && contextScope.allergies.length > 0 && (
                      <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-900/50">
                        <span className="text-[11px] font-semibold text-rose-300 uppercase tracking-wider block mb-1">
                          Known Allergies
                        </span>
                        <ul className="list-disc pl-4 space-y-0.5 text-rose-200">
                          {contextScope.allergies.map((a: unknown, idx: number) => (
                            <li key={idx}>
                              {typeof a === 'object' && a !== null && 'value' in a
                                ? String((a as { value: unknown }).value)
                                : String(a)}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {Array.isArray(contextScope.medications) && contextScope.medications.length > 0 && (
                      <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                          Active Medications
                        </span>
                        <ul className="list-disc pl-4 space-y-0.5 text-slate-300">
                          {contextScope.medications.map((m: unknown, idx: number) => (
                            <li key={idx}>
                              {typeof m === 'object' && m !== null && 'value' in m
                                ? String((m as { value: unknown }).value)
                                : String(m)}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {contextScope.clinical_summary ? (
                      <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                          Clinical Summary
                        </span>
                        <p className="text-slate-300 whitespace-pre-line leading-relaxed">
                          {String(contextScope.clinical_summary)}
                        </p>
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <p className="text-slate-500 italic">No extra scope provided.</p>
                )}
              </div>
            </div>
          )}

          {/* Right Drawer: Companion Chat & Real-Time Notes */}
          {activeDrawer === 'chat' && (
            <div className="w-80 sm:w-96 bg-slate-900 border-l border-slate-800 flex flex-col z-30 transition-all">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <MessageSquare className="w-4 h-4 text-teal-400" />
                  <h4 className="text-sm font-semibold text-white">Consultation Notes & Chat</h4>
                </div>
                <button
                  onClick={() => setActiveDrawer('none')}
                  className="text-slate-400 hover:text-white p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Chat Messages */}
              <div className="p-4 flex-1 overflow-y-auto space-y-3">
                {chatMessages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500">
                    <MessageSquare className="w-8 h-8 mb-2 opacity-50" />
                    <p className="text-xs">
                      Exchange real-time clinical notes, medication names, and dosages during the consultation.
                    </p>
                  </div>
                ) : (
                  chatMessages.map((msg) => (
                    <div
                      key={msg.id}
                      className={cn(
                        'flex flex-col max-w-[85%] rounded-xl px-3 py-2 text-xs space-y-1',
                        msg.isSelf
                          ? 'ml-auto bg-teal-600 text-white rounded-br-none'
                          : 'mr-auto bg-slate-800 text-slate-200 rounded-bl-none border border-slate-700'
                      )}
                    >
                      <div className="flex items-center justify-between space-x-2 text-[10px] opacity-75">
                        <span className="font-medium">{msg.sender}</span>
                        <span>{msg.time}</span>
                      </div>
                      <p className="break-words">{msg.text}</p>
                    </div>
                  ))
                )}
              </div>

              {/* Chat Input */}
              <form onSubmit={handleSendChat} className="p-3 border-t border-slate-800 flex items-center space-x-2">
                <input
                  type="text"
                  placeholder="Type a clinical note..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
                />
                <button
                  type="submit"
                  disabled={!chatInput.trim()}
                  className="p-2 rounded-lg bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white transition-colors"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </form>
            </div>
          )}
        </div>

        {/* Bottom Control Bar */}
        <div className="px-4 sm:px-6 py-3 bg-slate-950 border-t border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400 hidden sm:inline">Controls:</span>
            <button
              onClick={toggleAudio}
              className={cn(
                'flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-semibold border transition-all',
                audioEnabled
                  ? 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-white'
                  : 'bg-rose-600/20 hover:bg-rose-600/30 border-rose-500 text-rose-300'
              )}
            >
              {audioEnabled ? <Mic className="w-4 h-4 text-emerald-400" /> : <MicOff className="w-4 h-4 text-rose-400" />}
              <span>{audioEnabled ? 'Mute' : 'Unmute'}</span>
            </button>

            <button
              onClick={toggleVideo}
              className={cn(
                'flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-semibold border transition-all',
                videoEnabled
                  ? 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-white'
                  : 'bg-rose-600/20 hover:bg-rose-600/30 border-rose-500 text-rose-300'
              )}
            >
              {videoEnabled ? <Video className="w-4 h-4 text-emerald-400" /> : <VideoOff className="w-4 h-4 text-rose-400" />}
              <span>{videoEnabled ? 'Stop Video' : 'Start Video'}</span>
            </button>
          </div>

          {/* End Consultation Button */}
          <div>
            {!confirmEndOpen ? (
              <button
                onClick={() => setConfirmEndOpen(true)}
                disabled={isEnding}
                className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs sm:text-sm font-semibold shadow-lg shadow-rose-900/30 transition-all disabled:opacity-50"
              >
                <PhoneOff className="w-4 h-4" />
                <span>End Consultation</span>
              </button>
            ) : (
              <div className="flex items-center space-x-2 animate-in fade-in">
                <span className="text-xs text-rose-300 font-medium">Conclude session?</span>
                <button
                  onClick={handleEndConsultation}
                  disabled={isEnding}
                  className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition-colors"
                >
                  {isEnding ? 'Ending...' : 'Yes, End'}
                </button>
                <button
                  onClick={() => setConfirmEndOpen(false)}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
