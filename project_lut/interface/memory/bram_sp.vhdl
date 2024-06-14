library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity bram_sp is
	generic(
		width_g        : natural := 16;
		height_bits_g  : natural := 32;
		memory_size_g  : natural := 4800
		);
	port(
		clk_i  : in std_logic;
		addr_i : in std_logic_vector(height_bits_g - 1 downto 0) ;
		din_i  : in std_logic_vector(width_g-1 downto 0);
		dout_o : out std_logic_vector(width_g-1 downto 0);
		re_i   : in std_ulogic;
		we_i   : in std_ulogic
	);
end bram_sp;

architecture rtl of bram_sp is

	constant width_bytes_c : natural := width_g / 8;

	-- RAM type
    type ram_t is array(0 to (memory_size_g / width_bytes_c)) of std_logic_vector(width_g-1 downto 0);

	-- RAM instance
	--signal memory_s : ram_t := (others => (others => '0'));
	signal memory_s : ram_t;
	attribute ram_style : string;
	attribute ram_style of memory_s : signal is "block";
	attribute ram_decomp : string;
	attribute ram_decomp of memory_s : signal is "power";

	begin

	process (clk_i)
	begin
		if (rising_edge(clk_i)) then
			if we_i = '1' then
				memory_s(to_integer(unsigned(addr_i))) <= din_i;
			end if;
			if re_i = '1' then
			    if  to_integer(unsigned(addr_i)) < (memory_size_g / width_bytes_c) then
				    dout_o <= memory_s(to_integer(unsigned(addr_i)));
				else
				    dout_o <= (others => '0');
				end if;
			end if;
		end if;
	end process;

end rtl;