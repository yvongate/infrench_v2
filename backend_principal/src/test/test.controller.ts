import { Controller, Get, Post, Body } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Controller('test')
export class TestController {
    constructor(private prisma: PrismaService) { }

    @Get()
    async getAllTests() {
        return this.prisma.test.findMany();
    }

    @Post()
    async createTest(@Body() data: { message: string }) {
        return this.prisma.test.create({
            data: {
                message: data.message,
            },
        });
    }

    @Get('health')
    async healthCheck() {
        try {
            await this.prisma.$queryRaw`SELECT 1`;
            return { status: 'ok', message: 'Connexion Supabase réussie !' };
        } catch (error) {
            return { status: 'error', message: error.message };
        }
    }
}
