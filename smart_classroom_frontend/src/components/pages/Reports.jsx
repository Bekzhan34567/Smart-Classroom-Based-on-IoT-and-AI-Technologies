import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";

export default function Reports() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Отчеты</CardTitle>
        <CardDescription>Генерация и просмотр отчетов</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8">
          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Раздел отчетов</p>
          <p className="text-sm text-gray-400 mt-2">
            Доступно только для администраторов
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
