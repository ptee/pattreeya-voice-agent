'use client';

import { useEffect, useLayoutEffect, useMemo, useState } from 'react';
import { cva } from 'class-variance-authority';
import { LocalAudioTrack, LocalVideoTrack } from 'livekit-client';
import { useMaybeRoomContext, useMediaDeviceSelect } from '@livekit/components-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/livekit/select';
import { cn } from '@/lib/utils';

type DeviceSelectProps = React.ComponentProps<typeof SelectTrigger> & {
  kind: MediaDeviceKind;
  variant?: 'default' | 'small';
  track?: LocalAudioTrack | LocalVideoTrack | undefined;
  requestPermissions?: boolean;
  onMediaDeviceError?: (error: Error) => void;
  onDeviceListChange?: (devices: MediaDeviceInfo[]) => void;
  onActiveDeviceChange?: (deviceId: string) => void;
};

const selectVariants = cva(
  'w-full rounded-full px-3 py-2 text-sm cursor-pointer disabled:not-allowed',
  {
    variants: {
      size: {
        default: 'w-[180px]',
        sm: 'w-auto',
      },
    },
    defaultVariants: {
      size: 'default',
    },
  }
);

export function TrackDeviceSelect({
  kind,
  track,
  size = 'default',
  requestPermissions = false,
  onMediaDeviceError,
  onDeviceListChange,
  onActiveDeviceChange,
  ...props
}: DeviceSelectProps) {
  const room = useMaybeRoomContext();
  const [open, setOpen] = useState(false);
  const [requestPermissionsState, setRequestPermissionsState] = useState(requestPermissions);
  const { devices, activeDeviceId, setActiveMediaDevice } = useMediaDeviceSelect({
    room,
    kind,
    track,
    requestPermissions: requestPermissionsState,
    onError: onMediaDeviceError,
  });

  useEffect(() => {
    onDeviceListChange?.(devices);
  }, [devices, onDeviceListChange]);

  // When the select opens, ensure that media devices are re-requested in case when they were last
  // requested, permissions were not granted
  useLayoutEffect(() => {
    if (open) {
      setRequestPermissionsState(true);
    }
  }, [open]);

  const handleActiveDeviceChange = (deviceId: string) => {
    setActiveMediaDevice(deviceId);
    onActiveDeviceChange?.(deviceId);
  };

  // First filter out empty deviceIds, then remove duplicates
  const filteredDevices = useMemo(() => {
    // Filter out devices with empty deviceId
    const nonEmptyDevices = devices.filter((d) => d.deviceId !== '');
    
    // Remove duplicate devices based on deviceId
    const seen = new Map<string, MediaDeviceInfo>();
    const uniqueDevices: MediaDeviceInfo[] = [];
    
    for (const device of nonEmptyDevices) {
      // Create a unique key that combines deviceId, label, and kind for better deduplication
      const key = `${device.deviceId}-${device.label}-${device.kind}`;
      
      if (!seen.has(device.deviceId)) {
        seen.set(device.deviceId, device);
        uniqueDevices.push(device);
      } else {
        // Optional: Log duplicate detection for debugging
        console.warn(`Duplicate device detected: ${device.label} (${device.deviceId})`);
      }
    }
    
    return uniqueDevices;
  }, [devices]);

  if (filteredDevices.length < 2) {
    return null;
  }

  return (
    <Select
      open={open}
      value={activeDeviceId}
      onOpenChange={setOpen}
      onValueChange={handleActiveDeviceChange}
    >
      <SelectTrigger className={cn(selectVariants({ size }), props.className)}>
        {size !== 'sm' && (
          <SelectValue className="font-mono text-sm" placeholder={`Select a ${kind}`} />
        )}
      </SelectTrigger>
      <SelectContent>
        {filteredDevices.map((device) => (
          <SelectItem key={device.deviceId} value={device.deviceId} className="font-mono text-xs">
            {device.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
