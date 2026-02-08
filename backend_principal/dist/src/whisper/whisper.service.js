"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.WhisperService = void 0;
const common_1 = require("@nestjs/common");
const axios_1 = __importDefault(require("axios"));
const form_data_1 = __importDefault(require("form-data"));
const fs_1 = require("fs");
let WhisperService = class WhisperService {
    apiKey = process.env.DEEPINFRA_API_KEY || '';
    apiUrl = process.env.WHISPER_MODEL_URL ||
        'https://api.deepinfra.com/v1/openai/audio/transcriptions';
    async transcribeAudio(audioFilePath) {
        try {
            const formData = new form_data_1.default();
            formData.append('file', (0, fs_1.createReadStream)(audioFilePath));
            formData.append('model', 'openai/whisper-large-v3-turbo');
            const response = await axios_1.default.post(this.apiUrl, formData, {
                headers: {
                    ...formData.getHeaders(),
                    Authorization: `Bearer ${this.apiKey}`,
                },
            });
            return response.data.text || response.data.transcription || '';
        }
        catch (error) {
            console.error('Erreur lors de la transcription:', error.response?.data || error.message);
            throw new Error('Échec de la transcription audio');
        }
    }
};
exports.WhisperService = WhisperService;
exports.WhisperService = WhisperService = __decorate([
    (0, common_1.Injectable)()
], WhisperService);
//# sourceMappingURL=whisper.service.js.map