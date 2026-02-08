"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
var __param = (this && this.__param) || function (paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.TranscribeController = void 0;
const common_1 = require("@nestjs/common");
const platform_express_1 = require("@nestjs/platform-express");
const whisper_service_1 = require("./whisper.service");
const multer_1 = require("multer");
const path_1 = require("path");
const promises_1 = require("fs/promises");
let TranscribeController = class TranscribeController {
    whisperService;
    constructor(whisperService) {
        this.whisperService = whisperService;
    }
    async transcribeVideo(file) {
        if (!file) {
            throw new common_1.BadRequestException('Aucun fichier vidéo fourni');
        }
        try {
            const transcription = await this.whisperService.transcribeAudio(file.path);
            await (0, promises_1.unlink)(file.path);
            return {
                success: true,
                transcription,
                filename: file.originalname,
            };
        }
        catch (error) {
            try {
                await (0, promises_1.unlink)(file.path);
            }
            catch { }
            throw new common_1.BadRequestException(error.message || 'Erreur lors de la transcription');
        }
    }
};
exports.TranscribeController = TranscribeController;
__decorate([
    (0, common_1.Post)(),
    (0, common_1.UseInterceptors)((0, platform_express_1.FileInterceptor)('video', {
        storage: (0, multer_1.diskStorage)({
            destination: './uploads',
            filename: (req, file, cb) => {
                const randomName = Array(32)
                    .fill(null)
                    .map(() => Math.round(Math.random() * 16).toString(16))
                    .join('');
                cb(null, `${randomName}${(0, path_1.extname)(file.originalname)}`);
            },
        }),
        limits: {
            fileSize: 100 * 1024 * 1024,
        },
    })),
    __param(0, (0, common_1.UploadedFile)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Object]),
    __metadata("design:returntype", Promise)
], TranscribeController.prototype, "transcribeVideo", null);
exports.TranscribeController = TranscribeController = __decorate([
    (0, common_1.Controller)('transcribe'),
    __metadata("design:paramtypes", [whisper_service_1.WhisperService])
], TranscribeController);
//# sourceMappingURL=transcribe.controller.js.map