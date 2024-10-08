----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 2024/01/19 01:09:25
-- Design Name: 
-- Module Name: lut - Behavioral
-- Project Name: 
-- Target Devices: 
-- Tool Versions: 
-- Description: 
-- 
-- Dependencies: 
-- 
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
-- 
----------------------------------------------------------------------------------
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;
use work.my_package.all;

-- Uncomment the following library declaration if using
-- arithmetic functions with Signed or Unsigned values
--use IEEE.NUMERIC_STD.ALL;

-- Uncomment the following library declaration if instantiating
-- any Xilinx leaf cells in this code.
--library UNISIM;
--use UNISIM.VComponents.all;

entity lut is
    generic (lut_size : integer);
    port(
        index: in std_logic_vector(K-1 downto 0);
        output: out std_logic_vector(K-1 downto 0));
end lut;

architecture Behavioral of lut is

begin
    process(index)
    begin
--        if lut_size = 256 then
        case index is
            when "00000000" => output <= "00000000";
            when "00000001" => output <= "00000001";
            when "00000010" => output <= "00000010";
            when "00000011" => output <= "00000011";
            when "00000100" => output <= "00000100";
            when "00000101" => output <= "00000101";
            when "00000110" => output <= "00000110";
            when "00000111" => output <= "00000111";
            when "00001000" => output <= "00001000";
            when "00001001" => output <= "00001001";
            when "00001010" => output <= "00001010";
            when "00001011" => output <= "00001011";
            when "00001100" => output <= "00001100";
            when "00001101" => output <= "00001101";
            when "00001110" => output <= "00001110";
            when "00001111" => output <= "00001111";
            when "00010000" => output <= "00010000";
            when "00010001" => output <= "00010001";
            when "00010010" => output <= "00010010";
            when "00010011" => output <= "00010011";
            when "00010100" => output <= "00010100";
            when "00010101" => output <= "00010101";
            when "00010110" => output <= "00010110";
            when "00010111" => output <= "00010111";
            when "00011000" => output <= "00011000";
            when "00011001" => output <= "00011001";
            when "00011010" => output <= "00011010";
            when "00011011" => output <= "00011011";
            when "00011100" => output <= "00011100";
            when "00011101" => output <= "00011101";
            when "00011110" => output <= "00011110";
            when "00011111" => output <= "00011111";
            when "00100000" => output <= "00100000";
            when "00100001" => output <= "00100001";
            when "00100010" => output <= "00100010";
            when "00100011" => output <= "00100011";
            when "00100100" => output <= "00100100";
            when "00100101" => output <= "00100101";
            when "00100110" => output <= "00100110";
            when "00100111" => output <= "00100111";
            when "00101000" => output <= "00101000";
            when "00101001" => output <= "00101001";
            when "00101010" => output <= "00101010";
            when "00101011" => output <= "00101011";
            when "00101100" => output <= "00101100";
            when "00101101" => output <= "00101101";
            when "00101110" => output <= "00101110";
            when "00101111" => output <= "00101111";
            when "00110000" => output <= "00110000";
            when "00110001" => output <= "00110001";
            when "00110010" => output <= "00110010";
            when "00110011" => output <= "00110011";
            when "00110100" => output <= "00110100";
            when "00110101" => output <= "00110101";
            when "00110110" => output <= "00110110";
            when "00110111" => output <= "00110111";
            when "00111000" => output <= "00111000";
            when "00111001" => output <= "00111001";
            when "00111010" => output <= "00111010";
            when "00111011" => output <= "00111011";
            when "00111100" => output <= "00111100";
            when "00111101" => output <= "00111101";
            when "00111110" => output <= "00111110";
            when "00111111" => output <= "00111111";
            when "01000000" => output <= "01000000";
            when "01000001" => output <= "01000001";
            when "01000010" => output <= "01000010";
            when "01000011" => output <= "01000011";
            when "01000100" => output <= "01000100";
            when "01000101" => output <= "01000101";
            when "01000110" => output <= "01000110";
            when "01000111" => output <= "01000111";
            when "01001000" => output <= "01001000";
            when "01001001" => output <= "01001001";
            when "01001010" => output <= "01001010";
            when "01001011" => output <= "01001011";
            when "01001100" => output <= "01001100";
            when "01001101" => output <= "01001101";
            when "01001110" => output <= "01001110";
            when "01001111" => output <= "01001111";
            when "01010000" => output <= "01010000";
            when "01010001" => output <= "01010001";
            when "01010010" => output <= "01010010";
            when "01010011" => output <= "01010011";
            when "01010100" => output <= "01010100";
            when "01010101" => output <= "01010101";
            when "01010110" => output <= "01010110";
            when "01010111" => output <= "01010111";
            when "01011000" => output <= "01011000";
            when "01011001" => output <= "01011001";
            when "01011010" => output <= "01011010";
            when "01011011" => output <= "01011011";
            when "01011100" => output <= "01011100";
            when "01011101" => output <= "01011101";
            when "01011110" => output <= "01011110";
            when "01011111" => output <= "01011111";
            when "01100000" => output <= "01100000";
            when "01100001" => output <= "01100001";
            when "01100010" => output <= "01100010";
            when "01100011" => output <= "01100011";
            when "01100100" => output <= "01100100";
            when "01100101" => output <= "01100101";
            when "01100110" => output <= "01100110";
            when "01100111" => output <= "01100111";
            when "01101000" => output <= "01101000";
            when "01101001" => output <= "01101001";
            when "01101010" => output <= "01101010";
            when "01101011" => output <= "01101011";
            when "01101100" => output <= "01101100";
            when "01101101" => output <= "01101101";
            when "01101110" => output <= "01101110";
            when "01101111" => output <= "01101111";
            when "01110000" => output <= "01110000";
            when "01110001" => output <= "01110001";
            when "01110010" => output <= "01110010";
            when "01110011" => output <= "01110011";
            when "01110100" => output <= "01110100";
            when "01110101" => output <= "01110101";
            when "01110110" => output <= "01110110";
            when "01110111" => output <= "01110111";
            when "01111000" => output <= "01111000";
            when "01111001" => output <= "01111001";
            when "01111010" => output <= "01111010";
            when "01111011" => output <= "01111011";
            when "01111100" => output <= "01111100";
            when "01111101" => output <= "01111101";
            when "01111110" => output <= "01111110";
            when "01111111" => output <= "01111111";
            when "10000000" => output <= "10000000";
            when "10000001" => output <= "10000001";
            when "10000010" => output <= "10000010";
            when "10000011" => output <= "10000011";
            when "10000100" => output <= "10000100";
            when "10000101" => output <= "10000101";
            when "10000110" => output <= "10000110";
            when "10000111" => output <= "10000111";
            when "10001000" => output <= "10001000";
            when "10001001" => output <= "10001001";
            when "10001010" => output <= "10001010";
            when "10001011" => output <= "10001011";
            when "10001100" => output <= "10001100";
            when "10001101" => output <= "10001101";
            when "10001110" => output <= "10001110";
            when "10001111" => output <= "10001111";
            when "10010000" => output <= "10010000";
            when "10010001" => output <= "10010001";
            when "10010010" => output <= "10010010";
            when "10010011" => output <= "10010011";
            when "10010100" => output <= "10010100";
            when "10010101" => output <= "10010101";
            when "10010110" => output <= "10010110";
            when "10010111" => output <= "10010111";
            when "10011000" => output <= "10011000";
            when "10011001" => output <= "10011001";
            when "10011010" => output <= "10011010";
            when "10011011" => output <= "10011011";
            when "10011100" => output <= "10011100";
            when "10011101" => output <= "10011101";
            when "10011110" => output <= "10011110";
            when "10011111" => output <= "10011111";
            when "10100000" => output <= "10100000";
            when "10100001" => output <= "10100001";
            when "10100010" => output <= "10100010";
            when "10100011" => output <= "10100011";
            when "10100100" => output <= "10100100";
            when "10100101" => output <= "10100101";
            when "10100110" => output <= "10100110";
            when "10100111" => output <= "10100111";
            when "10101000" => output <= "10101000";
            when "10101001" => output <= "10101001";
            when "10101010" => output <= "10101010";
            when "10101011" => output <= "10101011";
            when "10101100" => output <= "10101100";
            when "10101101" => output <= "10101101";
            when "10101110" => output <= "10101110";
            when "10101111" => output <= "10101111";
            when "10110000" => output <= "10110000";
            when "10110001" => output <= "10110001";
            when "10110010" => output <= "10110010";
            when "10110011" => output <= "10110011";
            when "10110100" => output <= "10110100";
            when "10110101" => output <= "10110101";
            when "10110110" => output <= "10110110";
            when "10110111" => output <= "10110111";
            when "10111000" => output <= "10111000";
            when "10111001" => output <= "10111001";
            when "10111010" => output <= "10111010";
            when "10111011" => output <= "10111011";
            when "10111100" => output <= "10111100";
            when "10111101" => output <= "10111101";
            when "10111110" => output <= "10111110";
            when "10111111" => output <= "10111111";
            when "11000000" => output <= "11000000";
            when "11000001" => output <= "11000001";
            when "11000010" => output <= "11000010";
            when "11000011" => output <= "11000011";
            when "11000100" => output <= "11000100";
            when "11000101" => output <= "11000101";
            when "11000110" => output <= "11000110";
            when "11000111" => output <= "11000111";
            when "11001000" => output <= "11001000";
            when "11001001" => output <= "11001001";
            when "11001010" => output <= "11001010";
            when "11001011" => output <= "11001011";
            when "11001100" => output <= "11001100";
            when "11001101" => output <= "11001101";
            when "11001110" => output <= "11001110";
            when "11001111" => output <= "11001111";
            when "11010000" => output <= "11010000";
            when "11010001" => output <= "11010001";
            when "11010010" => output <= "11010010";
            when "11010011" => output <= "11010011";
            when "11010100" => output <= "11010100";
            when "11010101" => output <= "11010101";
            when "11010110" => output <= "11010110";
            when "11010111" => output <= "11010111";
            when "11011000" => output <= "11011000";
            when "11011001" => output <= "11011001";
            when "11011010" => output <= "11011010";
            when "11011011" => output <= "11011011";
            when "11011100" => output <= "11011100";
            when "11011101" => output <= "11011101";
            when "11011110" => output <= "11011110";
            when "11011111" => output <= "11011111";
            when "11100000" => output <= "11100000";
            when "11100001" => output <= "11100001";
            when "11100010" => output <= "11100010";
            when "11100011" => output <= "11100011";
            when "11100100" => output <= "11100100";
            when "11100101" => output <= "11100101";
            when "11100110" => output <= "11100110";
            when "11100111" => output <= "11100111";
            when "11101000" => output <= "11101000";
            when "11101001" => output <= "11101001";
            when "11101010" => output <= "11101010";
            when "11101011" => output <= "11101011";
            when "11101100" => output <= "11101100";
            when "11101101" => output <= "11101101";
            when "11101110" => output <= "11101110";
            when "11101111" => output <= "11101111";
            when "11110000" => output <= "11110000";
            when "11110001" => output <= "11110001";
            when "11110010" => output <= "11110010";
            when "11110011" => output <= "11110011";
            when "11110100" => output <= "11110100";
            when "11110101" => output <= "11110101";
            when "11110110" => output <= "11110110";
            when "11110111" => output <= "11110111";
            when "11111000" => output <= "11111000";
            when "11111001" => output <= "11111001";
            when "11111010" => output <= "11111010";
            when "11111011" => output <= "11111011";
            when "11111100" => output <= "11111100";
            when "11111101" => output <= "11111101";
            when "11111110" => output <= "11111110";
            when "11111111" => output <= "11111111";
            when others => output <= (others => '0'); -- Default case
        end case;
--        elsif lut_size = 128 then
            
    end process;
    
end Behavioral;