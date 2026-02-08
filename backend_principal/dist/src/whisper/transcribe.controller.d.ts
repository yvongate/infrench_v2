import { WhisperService } from './whisper.service';
export declare class TranscribeController {
    private readonly whisperService;
    constructor(whisperService: WhisperService);
    transcribeVideo(file: Express.Multer.File): Promise<{
        success: boolean;
        transcription: string;
        filename: string;
    }>;
}
