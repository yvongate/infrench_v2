import { PrismaService } from '../prisma/prisma.service';
export declare class TestController {
    private prisma;
    constructor(prisma: PrismaService);
    getAllTests(): Promise<{
        id: string;
        message: string;
        createdAt: Date;
        updatedAt: Date;
    }[]>;
    createTest(data: {
        message: string;
    }): Promise<{
        id: string;
        message: string;
        createdAt: Date;
        updatedAt: Date;
    }>;
    healthCheck(): Promise<{
        status: string;
        message: any;
    }>;
}
