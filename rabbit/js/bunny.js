// Bunny animation frames - combined module
// Re-exports walk and jump frames with names matching index.html

import { FRAMES as BUNNY_FRAMES_LEFT } from './walk/w60_frames.js';
import { FRAMES as BUNNY_FRAMES_RIGHT } from './walk/w60_right_frames.js';
import { FRAMES as BUNNY_JUMP_LEFT } from './jump/w60_frames.js';
import { FRAMES as BUNNY_JUMP_RIGHT } from './jump/w60_right_frames.js';

export { BUNNY_FRAMES_LEFT, BUNNY_FRAMES_RIGHT, BUNNY_JUMP_LEFT, BUNNY_JUMP_RIGHT };
