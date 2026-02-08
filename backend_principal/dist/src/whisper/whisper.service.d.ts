export declare class WhisperService {
    private readonly apiKey;
    private readonly apiUrl;
    transcribeAudio(audioFilePath: string): Promise<string>;
}
