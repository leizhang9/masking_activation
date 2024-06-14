library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.my_package.all;

entity random_generator is
    port (
        clk     : in  std_logic;
        reset   : in  std_logic;
        rnd_out : out std_logic_vector(K-1 downto 0)
    );
end entity;

architecture Behavioral of random_generator is
    signal lfsr : std_logic_vector(K-1 downto 0); 
    signal temp_rnd : integer range 0 to my_size-1;     -- Temporary variable for the random number in the range 0-6
    
    signal counter : unsigned(7 downto 0) := (others => '0');
    signal clk_out : STD_LOGIC;
begin

    process(clk, reset)
    begin
        if reset = '1' then
            counter <= (others => '0');  -- Reset counter when reset signal is asserted
            clk_out <= '0';         -- Reset output clock when reset signal is asserted
        elsif rising_edge(clk) then      -- Detect rising edge of input clock
            if counter = to_unsigned(my_size-1, 8) then  -- Check if counter reaches k-1
                counter <= (others => '0');       -- Reset counter
                clk_out <= not clk_out; -- Toggle output clock
            else
                counter <= counter + 1;  -- Increment counter
            end if;
        end if;
    end process;


    process(clk_out, reset)
    begin
        if reset = '1' then
            lfsr <= "00000001"; -- Non-zero initialization
        elsif rising_edge(clk_out) then
            -- Example LFSR update logic
            lfsr <= lfsr(6 downto 0) & (lfsr(7) xor lfsr(5) xor lfsr(4) xor lfsr(3));
        end if;
    end process;

    -- Map the 8-bit number to the range 0-6
    temp_rnd <= to_integer(unsigned(lfsr)) mod my_size;

    -- Convert integer to std_logic_vector
    rnd_out <= std_logic_vector(to_unsigned(temp_rnd, K));

end architecture;
