public class FunctionCallTest {
    public static void main(String[] args) {
        int result = add(5, 3);
        System.out.println(result);
        
        int doubled = multiply(10);
        System.out.println(doubled);
    }
    
    public static int add(int a, int b) {
        return a + b;
    }
    
    public static int multiply(int x) {
        return x * 2;
    }
}