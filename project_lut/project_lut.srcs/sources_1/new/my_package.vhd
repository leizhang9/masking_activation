----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 2024/01/20 01:50:53
-- Design Name: 
-- Module Name: my_package - Behavioral
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
use IEEE.std_logic_1164.all;
use IEEE.std_logic_arith.all;
use IEEE.std_logic_unsigned.all;
package my_package is
  constant K: integer := 8;  --data width
  constant my_size: integer := 64; 
  --modulo parameter, number between 0 and 2^K
  --32, 64, 128, 256
  constant M: std_logic_vector(K-1 downto 0) := conv_std_logic_vector(my_size, K);
end my_package;


